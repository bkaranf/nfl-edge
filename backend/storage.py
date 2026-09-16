"""Local durable storage; source caches and evaluations retain original timestamps."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
from uuid import uuid4

from backend.domain import Settings, iso


class Store:
    def __init__(self, path: str | Path | None = None):
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "SportsBetting"
        self.path = Path(path or os.environ.get("NFL_EDGE_DB", str(base / "nfl-edge.sqlite3")))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS games (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, payload TEXT, health TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, source TEXT NOT NULL, observed_at TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS idx_snapshots_observed ON snapshots(observed_at);
                CREATE TABLE IF NOT EXISTS manual_refs (id TEXT PRIMARY KEY, observed_at TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS evaluations (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS bets (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL);
                PRAGMA user_version=1;
                PRAGMA optimize;
            """)
            con.execute("INSERT OR IGNORE INTO settings VALUES (1, ?)", (Settings().model_dump_json(),))

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def settings(self) -> dict:
        with self.connect() as con:
            return json.loads(con.execute("SELECT payload FROM settings WHERE id=1").fetchone()[0])

    def set_settings(self, value: dict):
        with self.connect() as con:
            con.execute("UPDATE settings SET payload=? WHERE id=1", (json.dumps(value),))

    def games(self) -> dict[str, dict]:
        with self.connect() as con:
            return {r["id"]: json.loads(r["payload"]) for r in con.execute("SELECT * FROM games")}

    def put_games(self, games: list[dict]):
        with self.connect() as con:
            con.executemany("INSERT INTO games VALUES (?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                            [(g["id"], json.dumps(g)) for g in games])

    def sources(self) -> list[dict]:
        with self.connect() as con:
            return [{"id": r["id"], "data": json.loads(r["payload"]) if r["payload"] else None,
                     "health": json.loads(r["health"])} for r in con.execute("SELECT * FROM sources ORDER BY id")]

    def put_source(self, source: str, health: dict, payload: dict | None = None):
        with self.connect() as con:
            if payload is not None:
                con.execute("INSERT INTO sources VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, health=excluded.health",
                            (source, json.dumps(payload), json.dumps(health)))
                if source != "kalshi":
                    con.execute("INSERT INTO snapshots(source,observed_at,payload) VALUES (?,?,?)",
                                (source, payload["observed_at"], json.dumps(payload)))
            else:
                con.execute("INSERT INTO sources(id,health) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET health=excluded.health",
                            (source, json.dumps(health)))

    def quotes(self) -> list[dict]:
        quotes = [q for source in self.sources() if source["data"] for q in source["data"].get("quotes", [])]
        with self.connect() as con:
            refs = con.execute("SELECT payload FROM manual_refs ORDER BY observed_at DESC").fetchall()
        seen = set()
        for row in refs:
            ref = json.loads(row[0])
            key = (ref["game_id"], ref["book"], ref["market"], ref["line"])
            if key not in seen:
                quotes.extend(ref["quotes"])
                seen.add(key)
        return quotes

    def add_reference(self, ref: dict) -> str:
        ref_id = uuid4().hex
        with self.connect() as con:
            con.execute("INSERT INTO manual_refs VALUES (?,?,?)", (ref_id, ref["observed_at"], json.dumps(ref)))
        return ref_id

    def save_evaluation(self, payload: dict) -> str:
        evaluation_id = uuid4().hex
        with self.connect() as con:
            con.execute("INSERT INTO evaluations VALUES (?,?,?)", (evaluation_id, iso(), json.dumps(payload)))
        return evaluation_id

    def bets(self) -> list[dict]:
        with self.connect() as con:
            return [json.loads(r[0]) for r in con.execute("SELECT payload FROM bets ORDER BY created_at DESC")]

    def add_bet(self, bet: dict) -> dict:
        bet = {**bet, "id": uuid4().hex, "created_at": iso(), "status": "open", "settlement": None, "closing": None}
        with self.connect() as con:
            con.execute("INSERT INTO bets VALUES (?,?,?)", (bet["id"], bet["created_at"], json.dumps(bet)))
        return bet

    def update_bet(self, bet: dict):
        with self.connect() as con:
            con.execute("UPDATE bets SET payload=? WHERE id=?", (json.dumps(bet), bet["id"]))

    def historical_quotes(self, start: str, end: str) -> list[dict]:
        with self.connect() as con:
            batches = con.execute("SELECT payload FROM snapshots WHERE observed_at>=? AND observed_at<? ORDER BY observed_at DESC", (start, end)).fetchall()
            refs = con.execute("SELECT payload FROM manual_refs WHERE observed_at>=? AND observed_at<? ORDER BY observed_at DESC", (start, end)).fetchall()
        return [q for r in [*batches, *refs] for q in json.loads(r[0]).get("quotes", [])]
