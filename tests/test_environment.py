from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_environment.py"


def run_checker(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_checked_in_environment_matches_locks() -> None:
    result = run_checker()

    assert result.returncode == 0, result.stderr
    assert "Environment verification PASS" in result.stdout


def test_python_lock_version_mismatch_is_reported(tmp_path: Path) -> None:
    altered_lock = tmp_path / "requirements.lock"
    original = (ROOT / "requirements.lock").read_text(encoding="utf-8")
    altered_lock.write_text(
        original.replace("fastapi==0.141.1", "fastapi==0.0.0"),
        encoding="utf-8",
    )

    result = run_checker("--python-lock", str(altered_lock))

    assert result.returncode == 1
    assert "direct Python pin differs from lock for fastapi" in result.stderr
    assert "0.141.1 != 0.0.0" in result.stderr


def test_missing_required_frontend_package_is_reported(tmp_path: Path) -> None:
    installed_lock_path = ROOT / "frontend" / "node_modules" / ".package-lock.json"
    installed_lock = json.loads(installed_lock_path.read_text(encoding="utf-8"))
    del installed_lock["packages"]["node_modules/react"]
    altered_lock = tmp_path / "installed-package-lock.json"
    altered_lock.write_text(json.dumps(installed_lock), encoding="utf-8")

    result = run_checker("--frontend-installed-lock", str(altered_lock))

    assert result.returncode == 1
    assert "frontend direct dependency is not installed: react" in result.stderr
