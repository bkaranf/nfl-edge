"""Verify the checked-in dependency locks against the current local environment.

The verifier reads package metadata and version commands only. It does not import
the application, initialize storage, install packages, or access the network.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

from packaging.markers import default_environment
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name


EXACT_NPM_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


class CheckFailure(RuntimeError):
    """A reproducibility assertion did not hold."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckFailure(f"cannot read JSON file {path}: {exc}") from exc


def exact_python_requirement(text: str, context: str) -> tuple[str, str]:
    try:
        requirement = Requirement(text)
    except InvalidRequirement as exc:
        raise CheckFailure(f"invalid requirement in {context}: {text!r}") from exc

    specifiers = list(requirement.specifier)
    exact = (
        not requirement.extras
        and requirement.marker is None
        and requirement.url is None
        and len(specifiers) == 1
        and specifiers[0].operator == "=="
        and "*" not in specifiers[0].version
    )
    require(exact, f"{context} must use one exact == pin: {text!r}")
    return canonicalize_name(requirement.name), specifiers[0].version


def read_python_lock(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CheckFailure(f"cannot read Python lock {path}: {exc}") from exc

    locked: dict[str, str] = {}
    order: list[str] = []
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, version = exact_python_requirement(line, f"{path}:{line_number}")
        require(name not in locked, f"duplicate Python lock entry: {name}")
        locked[name] = version
        order.append(name)

    require(bool(locked), f"Python lock is empty: {path}")
    require(order == sorted(order), "Python lock entries must be sorted by normalized name")
    return locked


def check_python(root: Path, lock_path: Path) -> int:
    expected_python = (root / ".python-version").read_text(encoding="utf-8").strip()
    actual_python = ".".join(str(part) for part in sys.version_info[:3])
    require(
        actual_python == expected_python,
        f"Python runtime mismatch: expected {expected_python}, found {actual_python}",
    )

    with (root / "pyproject.toml").open("rb") as stream:
        project_data = tomllib.load(stream)["project"]
    require(
        project_data.get("requires-python") == f"=={expected_python}",
        "pyproject.toml requires-python must exactly match .python-version",
    )

    direct_texts = list(project_data.get("dependencies", []))
    direct_texts.extend(project_data.get("optional-dependencies", {}).get("test", []))
    direct: dict[str, str] = {}
    for text in direct_texts:
        name, version = exact_python_requirement(text, "pyproject.toml")
        require(name not in direct, f"duplicate direct Python dependency: {name}")
        direct[name] = version

    locked = read_python_lock(lock_path)
    for name, version in direct.items():
        require(name in locked, f"direct Python dependency missing from lock: {name}")
        require(
            locked[name] == version,
            f"direct Python pin differs from lock for {name}: {version} != {locked[name]}",
        )

    marker_environment = default_environment()
    marker_environment["extra"] = ""
    pending = list(direct)
    closure: set[str] = set()
    while pending:
        requested_name = canonicalize_name(pending.pop())
        if requested_name in closure:
            continue
        try:
            distribution = metadata.distribution(requested_name)
        except metadata.PackageNotFoundError as exc:
            raise CheckFailure(f"locked Python package is not installed: {requested_name}") from exc

        installed_name = canonicalize_name(distribution.metadata["Name"])
        installed_version = distribution.version
        require(installed_name == requested_name, f"unexpected distribution identity for {requested_name}")
        require(requested_name in locked, f"active transitive dependency missing from lock: {requested_name}")
        require(
            locked[requested_name] == installed_version,
            f"Python version mismatch for {requested_name}: lock has "
            f"{locked[requested_name]}, installed has {installed_version}",
        )
        closure.add(requested_name)

        for dependency_text in distribution.requires or []:
            dependency = Requirement(dependency_text)
            if dependency.marker is not None and not dependency.marker.evaluate(marker_environment):
                continue
            dependency_name = canonicalize_name(dependency.name)
            try:
                dependency_version = metadata.version(dependency_name)
            except metadata.PackageNotFoundError as exc:
                raise CheckFailure(
                    f"active dependency of {requested_name} is not installed: {dependency_name}"
                ) from exc
            require(
                not dependency.specifier or dependency_version in dependency.specifier,
                f"installed {dependency_name} {dependency_version} does not satisfy "
                f"{requested_name}'s requirement {dependency.specifier}",
            )
            pending.append(dependency_name)

    extra_entries = sorted(set(locked) - closure)
    require(
        not extra_entries,
        "Python lock contains packages outside the active project/test dependency closure: "
        + ", ".join(extra_entries),
    )
    return len(closure)


def command_version(command: str, root: Path) -> str:
    executable = shutil.which(command)
    require(executable is not None, f"required command is not on PATH: {command}")
    try:
        result = subprocess.run(
            [executable, "--version"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except OSError as exc:
        raise CheckFailure(f"could not run {command} --version: {exc}") from exc
    require(result.returncode == 0, f"{command} --version failed: {result.stderr.strip()}")
    return result.stdout.strip()


def check_npm_dependency_tree(frontend: Path) -> None:
    executable = shutil.which("npm")
    require(executable is not None, "required command is not on PATH: npm")
    try:
        result = subprocess.run(
            [
                executable,
                "--prefix",
                str(frontend),
                "ls",
                "--all",
                "--json",
                "--ignore-scripts",
                "--offline",
            ],
            cwd=frontend.parent,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except OSError as exc:
        raise CheckFailure(f"could not run offline npm dependency check: {exc}") from exc

    try:
        tree = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CheckFailure("offline npm dependency check returned invalid JSON") from exc
    require(isinstance(tree, dict), "offline npm dependency check returned a non-object result")
    problems = tree.get("problems", [])
    details = "; ".join(str(problem) for problem in problems)
    if not details:
        details = result.stderr.strip() or f"exit code {result.returncode}"
    require(
        result.returncode == 0 and not problems,
        f"offline npm dependency tree is incomplete or invalid: {details}",
    )


def check_frontend(root: Path, installed_lock_path: Path | None = None) -> tuple[int, int, str, str]:
    frontend = root / "frontend"
    manifest = read_json(frontend / "package.json")
    lock = read_json(frontend / "package-lock.json")
    if installed_lock_path is None:
        installed_lock_path = frontend / "node_modules" / ".package-lock.json"
    installed_lock = read_json(installed_lock_path)
    require(isinstance(manifest, dict), "frontend package.json must contain an object")
    require(isinstance(lock, dict), "frontend package-lock.json must contain an object")
    require(isinstance(installed_lock, dict), "installed frontend lock must contain an object")
    lock_packages = lock.get("packages", {})
    lock_root = lock_packages.get("")
    installed_packages = installed_lock.get("packages", {})
    require(lock.get("lockfileVersion") == 3, "frontend package-lock.json must use lockfileVersion 3")
    require(isinstance(lock_root, dict), "frontend lock is missing its root package record")
    require(isinstance(installed_packages, dict), "installed frontend lock has no package map")
    require(lock.get("name") == manifest.get("name"), "frontend manifest and lock names differ")
    require(lock.get("version") == manifest.get("version"), "frontend manifest and lock versions differ")
    require(lock_root.get("name") == manifest.get("name"), "frontend lock root name differs")
    require(lock_root.get("version") == manifest.get("version"), "frontend lock root version differs")

    expected_node = (root / ".node-version").read_text(encoding="utf-8").strip()
    engines = manifest.get("engines", {})
    require(engines.get("node") == expected_node, "package.json node engine must match .node-version")
    package_manager = manifest.get("packageManager", "")
    require(package_manager.startswith("npm@"), "package.json must pin packageManager to npm")
    expected_npm = package_manager.removeprefix("npm@")
    require(engines.get("npm") == expected_npm, "package.json npm engine must match packageManager")
    require(lock_root.get("engines") == engines, "frontend lock root engines differ from package.json")

    actual_node = command_version("node", root).removeprefix("v")
    actual_npm = command_version("npm", root)
    require(actual_node == expected_node, f"Node runtime mismatch: expected {expected_node}, found {actual_node}")
    require(actual_npm == expected_npm, f"npm runtime mismatch: expected {expected_npm}, found {actual_npm}")

    direct_count = 0
    for section in ("dependencies", "devDependencies"):
        manifest_dependencies = manifest.get(section, {})
        require(
            lock_root.get(section, {}) == manifest_dependencies,
            f"frontend lock root {section} differs from package.json",
        )
        for name, expected_version in manifest_dependencies.items():
            direct_count += 1
            require(
                bool(EXACT_NPM_VERSION.fullmatch(expected_version)),
                f"frontend direct dependency must be an exact version: {name}={expected_version!r}",
            )
            package_path = f"node_modules/{name}"
            locked_package = lock_packages.get(package_path)
            require(isinstance(locked_package, dict), f"frontend dependency missing from lock: {name}")
            require(
                locked_package.get("version") == expected_version,
                f"frontend direct lock mismatch for {name}: expected {expected_version}, "
                f"found {locked_package.get('version')}",
            )
            installed_package = installed_packages.get(package_path)
            require(
                isinstance(installed_package, dict),
                f"frontend direct dependency is not installed: {name}",
            )
            require(
                installed_package.get("version") == expected_version,
                f"installed frontend direct version mismatch for {name}: expected "
                f"{expected_version}, found {installed_package.get('version')}",
            )
            package_manifest = read_json(frontend / package_path / "package.json")
            require(
                package_manifest.get("version") == expected_version,
                f"installed frontend package manifest mismatch for {name}",
            )

    installed_count = 0
    for package_path, installed_record in installed_packages.items():
        if not package_path:
            continue
        installed_count += 1
        locked_record = lock_packages.get(package_path)
        require(isinstance(locked_record, dict), f"installed frontend package is absent from lock: {package_path}")
        for field in ("version", "resolved", "integrity"):
            if field in installed_record:
                require(
                    installed_record[field] == locked_record.get(field),
                    f"installed frontend {field} differs from lock for {package_path}",
                )
        package_manifest = read_json(frontend / package_path / "package.json")
        require(
            package_manifest.get("version") == locked_record.get("version"),
            f"installed frontend version differs from lock for {package_path}",
        )

    check_npm_dependency_tree(frontend)
    return direct_count, installed_count, actual_node, actual_npm


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_root, help="repository root")
    parser.add_argument(
        "--python-lock",
        type=Path,
        default=None,
        help="alternate Python lock path, useful for verification probes",
    )
    parser.add_argument(
        "--frontend-installed-lock",
        type=Path,
        default=None,
        help="alternate installed frontend lock path, useful for verification probes",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    lock_path = args.python_lock.resolve() if args.python_lock else root / "requirements.lock"
    installed_lock_path = (
        args.frontend_installed_lock.resolve() if args.frontend_installed_lock else None
    )
    try:
        python_count = check_python(root, lock_path)
        direct_count, installed_count, node_version, npm_version = check_frontend(
            root, installed_lock_path
        )
    except (CheckFailure, OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        print(f"Environment verification FAIL: {exc}", file=sys.stderr)
        return 1

    print("Environment verification PASS")
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}: {python_count} locked project/test distributions")
    print(
        f"Node {node_version} / npm {npm_version}: {direct_count} exact direct dependencies; "
        f"{installed_count} installed packages match package-lock.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
