"""Bounded public collection and local closing-price capture."""
import asyncio
from datetime import timedelta
import logging

import httpx

from backend.domain import Pick, QuoteInput, dt, iso, utcnow
from backend.engine import estimate, make_board, returns, stake_cap
from backend.providers import fetch_bovada, fetch_espn, fetch_kalshi, parse_kalshi
from backend.storage import Store

log = logging.getLogger(__name__)
SOURCE_INFO = {
    "espn": {"name": "ESPN / DraftKings", "kind": "Redistributed sportsbook", "url": "https://www.espn.com/nfl/odds",
             "note": "DraftKings counts once. Upstream quote age is unavailable; research evidence only."},
    "bovada": {"name": "Bovada", "kind": "Direct public sportsbook board", "url": "https://www.bovada.lv/sports/football/nfl",
               "note": "Reference prices only. Event modification time is separate from board observation time."},
    "kalshi": {"name": "Kalshi", "kind": "Exchange comparison", "url": "https://docs.kalshi.com/getting_started/quick_start_market_data",
               "note": "Ask prices exclude fees and are not Underdog quotes. Does not count as a sportsbook vote."},
}


class Service:
    def __init__(self, store: Store):
        self.store = store
        self.lock = asyncio.Lock()
        self.last_attempt = None

    async def refresh(self) -> dict:
        if self.lock.locked():
            return {"status": "running"}
        if self.last_attempt and (utcnow() - self.last_attempt).total_seconds() < 60:
            return {"status": "cooldown", "retry_seconds": max(1, round(60-(utcnow()-self.last_attempt).total_seconds()))}
        async with self.lock:
            self.last_attempt = utcnow()
            async with httpx.AsyncClient(timeout=25, follow_redirects=True,
                                         headers={"User-Agent": "NFLEdgeLocal/0.1 (personal read-only research)", "Accept": "application/json"}) as client:
                results = await asyncio.gather(fetch_bovada(client, self.last_attempt), fetch_espn(client, self.last_attempt),
                                               fetch_kalshi(client, self.last_attempt), return_exceptions=True)
            games = self.store.games()
            # ESPN supplies schedule state and postseason metadata when available.
            for result in results[:2]:
                if isinstance(result, dict):
                    games.update({g["id"]: g for g in result["games"]})
            self.store.put_games(list(games.values()))
            for source, result in zip(("bovada", "espn", "kalshi"), results):
                if isinstance(result, Exception):
                    log.warning("%s refresh failed: %s", source, result)
                    self.store.put_source(source, {"status": "error", "attempted_at": iso(self.last_attempt),
                                                   "error": f"{type(result).__name__}: {str(result)[:250]}"})
                    continue
                if source == "kalshi":
                    raw_count = len(result["raw_markets"])
                    result = {"quotes": parse_kalshi(result["raw_markets"], list(games.values())),
                              "observed_at": result["observed_at"], "raw_market_count": raw_count}
                else:
                    source_games = {g["id"]: g for g in result["games"]}
                    compatible = {key for key, g in source_games.items()
                                  if abs((dt(g["start_time"])-dt(games[key]["start_time"])).total_seconds()) <= 900}
                    result["quotes"] = [q for q in result["quotes"] if q["game_id"] in compatible]
                    result["schedule_conflicts"] = len(source_games) - len(compatible)
                quotes = result["quotes"]
                self.store.put_source(source, {"status": "partial" if result.get("partial") else "ok",
                    "attempted_at": iso(self.last_attempt), "error": None}, result)
            self.capture_closing()
            return {"status": "complete", "sources": self.sources()}

    async def loop(self):
        while True:
            try:
                await self.refresh()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Collection cycle failed")
            await asyncio.sleep(300)

    def sources(self) -> list[dict]:
        stored = {s["id"]: s for s in self.store.sources()}
        sources = []
        for key, info in SOURCE_INFO.items():
            s = stored.get(key, {})
            data = s.get("data") or {}
            quotes = data.get("quotes", [])
            sources.append({"id": key, **info, **s.get("health", {"status": "pending"}),
                            "last_success": data.get("observed_at"), "quote_count": len(quotes),
                            "game_count": len({q["game_id"] for q in quotes}),
                            "markets": sorted({q["market"] for q in quotes}),
                            "skipped": data.get("skipped", 0), "schedule_conflicts": data.get("schedule_conflicts", 0)})
        return sources

    def board(self) -> dict:
        settings, bets = self.store.settings(), self.store.bets()
        return {"as_of": iso(), "refreshing": self.lock.locked(), "sources": self.sources(),
                "settings": settings, "rows": make_board(self.store.games(), self.store.quotes(), settings),
                "exposure": {mode: stake_cap(settings, bets, "", mode) for mode in ("paper", "actual")}}

    def capture_closing(self):
        games = self.store.games()
        for bet in self.store.bets():
            if bet.get("closing") is not None:
                continue
            g = games.get(bet["quote"]["game_id"], bet["game"])
            start = dt(g["start_time"])
            if start > utcnow():
                continue
            quotes = self.store.historical_quotes(iso(start-timedelta(minutes=5)), iso(start))
            quotes = [q for q in quotes if start-timedelta(minutes=5) <= dt(q["observed_at"]) < start]
            pick = Pick(**{k: bet["quote"][k] for k in ("game_id", "market", "side", "line")})
            settings = {**bet["evaluation"]["settings"], "max_age_seconds": 300}
            prob = estimate(quotes, pick, settings, start)
            prob["is_moneyline"] = pick.market == "moneyline"
            q = QuoteInput(**bet["quote"])
            scenarios = returns(prob, g, float(q.winning_payout), float(q.push_return) if q.push_return is not None else None, settings)
            if scenarios:
                value = min(s["expected_return"] for s in scenarios)
                bet["closing"] = {"status": "supported" if prob["enough"] else "indicative", "captured_at": iso(),
                                  "at": iso(start), "probability": prob,
                                  "roi_pct": (value/float(q.total_cost)-1)*100,
                                  "description": "Estimated return at the final captured pregame benchmark, after entry cost. Not a profit guarantee."}
            else:
                bet["closing"] = {"status": "unavailable", "captured_at": iso(), "reason": "No comparable benchmark captured in the last five minutes before kickoff."}
            self.store.update_bet(bet)
