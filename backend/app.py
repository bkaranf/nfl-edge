from contextlib import asynccontextmanager, suppress
import asyncio
import csv
from io import StringIO
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from backend.domain import BOOKS, QuoteInput, ReferenceInput, SaveBet, Settings, Settlement, age, american_to_decimal, iso
from backend.engine import evaluate
from backend.providers import quote
from backend.service import Service
from backend.storage import Store


def create_app(db_path=None, collect=True):
    store = Store(db_path)
    service = Service(store)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(service.loop()) if collect and os.environ.get("NFL_EDGE_NO_COLLECT") != "1" else None
        yield
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    app = FastAPI(title="NFL Edge", version="0.1.0", lifespan=lifespan)
    app.state.store, app.state.service = store, service

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        if request.url.hostname not in {"127.0.0.1", "localhost", "::1", "testserver"}:
            return JSONResponse({"detail": "This app accepts local requests only."}, status_code=403)
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
            from urllib.parse import urlparse
            if urlparse(origin).hostname not in {"127.0.0.1", "localhost", "::1"}:
                return JSONResponse({"detail": "Cross-site writes are disabled."}, status_code=403)
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def get_game(game_id):
        g = store.games().get(game_id)
        if not g:
            raise HTTPException(404, "Unknown game; refresh the board.")
        return g

    @app.get("/api/health")
    def health():
        return {"status": "ok", "app": "nfl-edge", "version": "0.1.0"}

    @app.get("/api/board")
    def board():
        return service.board()

    @app.get("/api/sources")
    def sources():
        return {"sources": service.sources(), "manual_books": BOOKS}

    @app.post("/api/refresh")
    async def refresh():
        return await service.refresh()

    @app.get("/api/settings")
    def settings():
        return store.settings()

    @app.put("/api/settings")
    def update_settings(value: Settings):
        store.set_settings(value.model_dump(mode="json"))
        return store.settings()

    @app.post("/api/references", status_code=201)
    def add_reference(value: ReferenceInput):
        g = get_game(value.game_id)
        if not 0 <= age(iso(value.observed_at)) <= 86400:
            raise HTTPException(422, "Reference time must be within the past 24 hours.")
        observed, batch = iso(value.observed_at), uuid4().hex
        a, b = ("over", "under") if value.market == "total" else ("home", "away")
        quotes = [quote(g, "manual", value.book, value.market, side,
                        -value.line if value.market == "spread" and side == "away" else value.line,
                        american_to_decimal(price), observed, batch, kind="manual")
                  for side, price in ((a, value.price_a), (b, value.price_b))]
        ref = {**value.model_dump(mode="json"), "observed_at": observed, "quotes": quotes}
        return {"id": store.add_reference(ref)}

    @app.post("/api/evaluate")
    def check_quote(value: QuoteInput):
        result = evaluate(value, get_game(value.game_id), store.quotes(), store.settings(), store.bets())
        result["id"] = store.save_evaluation({"quote": value.model_dump(mode="json"), "result": result})
        return result

    @app.get("/api/bets")
    def bets():
        return store.bets()

    @app.post("/api/bets", status_code=201)
    def save_bet(value: SaveBet):
        if value.mode == "actual" and not value.placed_confirmed:
            raise HTTPException(422, "Confirm this was already placed manually and these are its accepted values.")
        raw = value.model_dump(exclude={"placed_confirmed", "notes"})
        q = QuoteInput(**raw)
        g = get_game(q.game_id)
        result = evaluate(q, g, store.quotes(), store.settings(), store.bets())
        return store.add_bet({"quote": q.model_dump(mode="json"), "game": g, "evaluation": result,
                              "notes": value.notes, "audit": []})

    @app.post("/api/bets/{bet_id}/settle")
    def settle(bet_id: str, value: Settlement):
        bet = next((b for b in store.bets() if b["id"] == bet_id), None)
        if not bet:
            raise HTTPException(404, "Bet not found.")
        if bet.get("settlement"):
            bet["audit"].append({"at": iso(), "previous_settlement": bet["settlement"]})
        from backend.domain import cents
        bet["settlement"] = {**value.model_dump(mode="json"), "at": iso(),
                             "pnl": (cents(value.returned)-cents(bet["quote"]["total_cost"]))/100}
        bet["status"] = "settled"
        store.update_bet(bet)
        return bet

    @app.get("/api/export.csv")
    def export():
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["id", "created_at", "mode", "game", "market", "side", "line", "total_cost", "winning_payout",
                         "exchange", "entry_estimated_roi_pct", "entry_qualified", "status", "returned", "pnl", "closing_status", "closing_roi_pct", "notes"])
        for b in store.bets():
            q, e, settlement, close = b["quote"], b["evaluation"], b.get("settlement") or {}, b.get("closing") or {}
            notes = b["notes"]
            if notes.lstrip().startswith(("=", "+", "-", "@")):
                notes = "'" + notes
            writer.writerow([b["id"], b["created_at"], q["mode"], q["game_id"], q["market"], q["side"], q["line"],
                             q["total_cost"], q["winning_payout"], q["exchange"], (e.get("net") or {}).get("roi_pct"), e["qualified"],
                             b["status"], settlement.get("returned"), settlement.get("pnl"), close.get("status"), close.get("roi_pct"), notes])
        return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="nfl-edge-journal.csv"'})

    dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/favicon.svg")
        def favicon():
            return FileResponse(dist / "favicon.svg")

        @app.get("/")
        def index():
            return FileResponse(dist / "index.html")
    return app


app = create_app()
