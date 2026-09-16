import os
from pathlib import Path
import tempfile


_test_data = tempfile.TemporaryDirectory(prefix="nfl-edge-pytest-")
os.environ["NFL_EDGE_DB"] = str(Path(_test_data.name) / "nfl-edge.sqlite3")
os.environ["NFL_EDGE_NO_COLLECT"] = "1"
