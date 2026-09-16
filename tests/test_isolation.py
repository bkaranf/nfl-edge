import asyncio
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from fastapi.testclient import TestClient
import pytest

from backend.app import create_app


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_import_does_not_touch_the_default_database(tmp_path):
    local_app_data = tmp_path / "local-app-data"
    local_app_data.mkdir()
    sentinel = local_app_data / "sentinel"
    sentinel.write_bytes(b"must remain unchanged")
    before = sentinel.stat()

    env = os.environ.copy()
    env.pop("NFL_EDGE_DB", None)
    env["LOCALAPPDATA"] = str(local_app_data)
    env["NFL_EDGE_NO_COLLECT"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import backend.app; "
                "assert backend.app.app.state.store is None; "
                "assert backend.app.app.state.service is None"
            ),
        ],
        cwd=REPOSITORY_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert not (local_app_data / "SportsBetting").exists()
    assert sentinel.read_bytes() == b"must remain unchanged"
    after = sentinel.stat()
    assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns)


def test_import_preserves_an_existing_default_database(tmp_path):
    local_app_data = tmp_path / "local-app-data"
    database = local_app_data / "SportsBetting" / "nfl-edge.sqlite3"
    database.parent.mkdir(parents=True)
    database.write_bytes(b"sentinel user database bytes")
    before = database.stat()

    env = os.environ.copy()
    env.pop("NFL_EDGE_DB", None)
    env["LOCALAPPDATA"] = str(local_app_data)
    env["NFL_EDGE_NO_COLLECT"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import backend.app; "
                "assert backend.app.app.state.store is None; "
                "assert backend.app.app.state.service is None"
            ),
        ],
        cwd=REPOSITORY_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert database.read_bytes() == b"sentinel user database bytes"
    after = database.stat()
    assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns)


def test_pytest_collection_preserves_an_existing_default_database(tmp_path):
    local_app_data = tmp_path / "local-app-data"
    database = local_app_data / "SportsBetting" / "nfl-edge.sqlite3"
    database.parent.mkdir(parents=True)
    database.write_bytes(b"sentinel user database bytes")
    before = database.stat()

    env = os.environ.copy()
    env.pop("NFL_EDGE_DB", None)
    env["LOCALAPPDATA"] = str(local_app_data)
    env["NFL_EDGE_NO_COLLECT"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=REPOSITORY_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert "tests/test_isolation.py::test_import_preserves_an_existing_default_database" in result.stdout
    assert "tests/test_isolation.py::test_collector_stops_when_lifespan_raises" in result.stdout
    assert database.read_bytes() == b"sentinel user database bytes"
    after = database.stat()
    assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns)


def test_pytest_sets_a_temporary_database_before_test_imports():
    database = Path(os.environ["NFL_EDGE_DB"]).resolve()

    assert Path(tempfile.gettempdir()).resolve() in database.parents
    assert database.name == "nfl-edge.sqlite3"
    assert not database.exists()


def test_no_path_factory_initializes_only_during_lifespan(tmp_path, monkeypatch):
    database = tmp_path / "runtime" / "nfl-edge.sqlite3"
    default_root = tmp_path / "default-local-app-data"
    monkeypatch.setenv("NFL_EDGE_DB", str(database))
    monkeypatch.setenv("LOCALAPPDATA", str(default_root))

    application = create_app(collect=False)

    assert application.state.store is None
    assert application.state.service is None
    assert not database.exists()
    assert not default_root.exists()

    with TestClient(application) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        assert application.state.store.path == database

    assert database.is_file()
    assert not (default_root / "SportsBetting").exists()


def test_explicit_factory_path_never_uses_the_default(tmp_path, monkeypatch):
    database = tmp_path / "explicit" / "nfl-edge.sqlite3"
    default_root = tmp_path / "default-local-app-data"
    monkeypatch.delenv("NFL_EDGE_DB", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(default_root))

    application = create_app(database, collect=False)

    assert application.state.store.path == database
    assert database.is_file()
    assert not (default_root / "SportsBetting").exists()
    with TestClient(application) as client:
        assert client.get("/api/health").status_code == 200


def test_collector_stops_when_lifespan_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("NFL_EDGE_NO_COLLECT", raising=False)
    application = create_app(tmp_path / "collector.sqlite3", collect=True)
    started = None
    stopped = None

    async def scenario():
        nonlocal started, stopped
        started = asyncio.Event()
        stopped = asyncio.Event()

        async def synthetic_loop():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()

        application.state.service.loop = synthetic_loop
        async with application.router.lifespan_context(application):
            await asyncio.wait_for(started.wait(), timeout=1)
            raise RuntimeError("synthetic lifespan failure")

    with pytest.raises(RuntimeError, match="synthetic lifespan failure"):
        asyncio.run(scenario())
    assert stopped.is_set()
