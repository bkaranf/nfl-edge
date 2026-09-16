"""Independent read-only public-data collectors. No login, trading, or proxy bypass."""
import asyncio
from datetime import UTC, datetime, timedelta
import re

import httpx

from backend.domain import EASTERN, TEAMS, american_to_decimal, dt, game, iso, team_code, utcnow

ESPN = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
BOVADA = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/football/nfl?lang=en"
KALSHI = "https://external-api.kalshi.com/trade-api/v2"


def quote(g: dict, source: str, book: str, market: str, side: str, line: float | None,
          price: float, observed: str, batch: str, **extras) -> dict:
    if not 1 < float(price) <= 10001:
        raise ValueError("Invalid decimal price")
    return {"game_id": g["id"], "source": source, "book": book, "market": market,
            "side": side, "line": line, "decimal_price": float(price), "observed_at": observed,
            "source_time": None, "batch": batch, "kind": "direct", "status": "open", **extras}


async def get_json(client: httpx.AsyncClient, url: str, params: dict | None = None):
    for attempt in range(2):
        response = await client.get(url, params=params)
        if response.status_code >= 500 and attempt == 0:
            await asyncio.sleep(0.6)
            continue
        response.raise_for_status()
        return response.json(), iso()
    raise RuntimeError("Source did not return data")


def parse_espn(data: dict, observed: str) -> dict:
    if not isinstance(data.get("events"), list):
        raise ValueError("ESPN response has no events list")
    games, quotes, skipped = [], [], 0
    for event in data["events"]:
        try:
            competition = event["competitions"][0]
            sides = {p["homeAway"]: p for p in competition["competitors"]}
            state = event.get("status", {}).get("type", {}).get("state", "pre")
            g = game(sides["home"]["team"]["displayName"], sides["away"]["team"]["displayName"], event["date"],
                     status={"pre": "scheduled", "in": "live", "post": "final"}.get(state, "scheduled"),
                     season_type="POST" if event.get("season", data.get("season", {})).get("type") == 3 else "REG",
                     espn_id=event["id"], week=event.get("week", data.get("week", {})).get("number"),
                     home_score=int(sides["home"].get("score", 0)), away_score=int(sides["away"].get("score", 0)))
            games.append(g)
            if state != "pre":
                continue
            for offer in competition.get("odds", []):
                provider = offer.get("provider", {})
                book = provider.get("displayName") or provider.get("name")
                if not book:
                    continue
                for key, market, outcomes in [("moneyline", "moneyline", ("home", "away")),
                                              ("pointSpread", "spread", ("home", "away")),
                                              ("total", "total", ("over", "under"))]:
                    for side in outcomes:
                        phase = offer.get(key, {}).get(side, {}).get("close", {})
                        if not phase.get("odds"):
                            continue
                        price = 100 if str(phase["odds"]).upper() == "EVEN" else float(phase["odds"])
                        line = None
                        if market != "moneyline":
                            if phase.get("line") is None:
                                continue
                            line = float(str(phase["line"]).lstrip("ouOU"))
                        quotes.append(quote(g, "espn", book, market, side, line, american_to_decimal(price), observed,
                                            f"espn:{event['id']}:{observed}", kind="redistributed", main=True))
        except (KeyError, IndexError, ValueError, TypeError):
            skipped += 1
    return {"games": games, "quotes": quotes, "observed_at": observed, "skipped": skipped}


async def fetch_espn(client: httpx.AsyncClient, now: datetime) -> dict:
    semaphore = asyncio.Semaphore(3)

    async def fetch_day(offset):
        async with semaphore:
            day = now.astimezone(EASTERN).date() + timedelta(days=offset)
            payload, observed = await get_json(client, ESPN, {"dates": day.strftime("%Y%m%d")})
            return parse_espn(payload, observed)

    results = await asyncio.gather(*(fetch_day(i) for i in range(-1, 8)), return_exceptions=True)
    good = [r for r in results if isinstance(r, dict)]
    if not good:
        raise RuntimeError("ESPN daily requests failed")
    games = {g["id"]: g for r in good for g in r["games"]}
    quotes = {(q["game_id"], q["book"], q["market"], q["side"], q["line"]): q for r in good for q in r["quotes"]}
    return {"games": list(games.values()), "quotes": list(quotes.values()), "observed_at": iso(),
            "skipped": sum(r["skipped"] for r in good), "partial": len(good) < len(results)}


def parse_bovada(data: list, observed: str) -> dict:
    if not isinstance(data, list) or any(not isinstance(item.get("events"), list) for item in data):
        raise ValueError("Bovada response has no event groups")
    games, quotes, skipped = [], [], 0
    for group in data:
        for event in group["events"]:
            try:
                if event.get("type") != "GAMEEVENT" or event.get("live"):
                    continue
                home = next(c["name"] for c in event["competitors"] if c.get("home") is True)
                away = next(c["name"] for c in event["competitors"] if c.get("home") is False)
                g = game(home, away, datetime.fromtimestamp(event["startTime"] / 1000, UTC))
                games.append(g)
                modified = iso(datetime.fromtimestamp(event["lastModified"] / 1000, UTC)) if event.get("lastModified") else None
                for display in event.get("displayGroups", []):
                    for market in display.get("markets", []):
                        period = market.get("period", {})
                        if market.get("status") != "O" or period.get("description") != "Game" or period.get("live"):
                            continue
                        kind = {"Moneyline": "moneyline", "Point Spread": "spread", "Spread": "spread",
                                "Total": "total", "Total Points": "total"}.get(market.get("description"))
                        if not kind:
                            continue
                        for outcome in market.get("outcomes", []):
                            if outcome.get("status") != "O":
                                continue
                            side_type = outcome.get("type")
                            if kind == "total":
                                side = "over" if side_type == "O" else "under" if side_type == "U" else None
                            else:
                                side = "home" if side_type == "H" else "away" if side_type == "A" else None
                                if side is None:
                                    code = team_code(outcome["description"])
                                    side = "home" if code == g["home"] else "away" if code == g["away"] else None
                            if side is None:
                                continue
                            price = outcome["price"]
                            line = float(price["handicap"]) if kind != "moneyline" and "handicap" in price else None
                            if kind != "moneyline" and line is None:
                                continue
                            quotes.append(quote(g, "bovada", "Bovada", kind, side, line, float(price["decimal"]), observed,
                                                f"bovada:{market['id']}:{observed}", source_time=modified,
                                                main=display.get("description") == "Game Lines"))
            except (ValueError, TypeError, KeyError, StopIteration):
                skipped += 1
    return {"games": games, "quotes": quotes, "observed_at": observed, "skipped": skipped, "partial": False}


async def fetch_bovada(client: httpx.AsyncClient, now: datetime) -> dict:
    payload, observed = await get_json(client, BOVADA)
    return parse_bovada(payload, observed)


async def fetch_kalshi(client: httpx.AsyncClient, now: datetime) -> dict:
    async def series(ticker):
        markets, cursor = [], None
        for _ in range(8):
            params = {"series_ticker": ticker, "status": "open", "limit": 1000}
            if cursor:
                params["cursor"] = cursor
            data, observed = await get_json(client, f"{KALSHI}/markets", params)
            if not isinstance(data.get("markets"), list):
                raise ValueError("Kalshi response has no markets list")
            markets.extend({**m, "observed_at": observed} for m in data["markets"])
            next_cursor = data.get("cursor")
            if not next_cursor:
                return markets
            if next_cursor == cursor:
                raise ValueError("Kalshi returned a repeated pagination cursor")
            cursor = next_cursor
        raise ValueError("Kalshi pagination exceeded the bounded collection budget")

    batches = await asyncio.gather(*(series(t) for t in ("KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL")))
    return {"raw_markets": [m for batch in batches for m in batch], "observed_at": iso()}


def parse_kalshi(markets: list[dict], games: list[dict]) -> list[dict]:
    output = []
    for market in markets:
        try:
            if market.get("status") != "active":
                continue
            ticker = market["ticker"]
            event = ticker.split("-")[1]
            when = datetime.strptime(event[:7], "%y%b%d").date()
            teams_part = event[7:]
            # Ticker team codes can include JAC/LA; compare the entire two-team token.
            candidates = []
            for g in games:
                if dt(g["start_time"]).astimezone(EASTERN).date() != when:
                    continue
                aliases = lambda code: {code, {"JAX": "JAC", "LAR": "LA", "WAS": "WSH"}.get(code, code)}
                valid = {a + h for a in aliases(g["away"]) for h in aliases(g["home"])} | {h + a for a in aliases(g["away"]) for h in aliases(g["home"])}
                if teams_part in valid:
                    candidates.append(g)
            if len(candidates) != 1:
                continue
            g = candidates[0]
            prefix = ticker.split("-")[0]
            kind = {"KXNFLGAME": "moneyline", "KXNFLSPREAD": "spread", "KXNFLTOTAL": "total"}.get(prefix)
            if not kind:
                continue
            if kind == "total":
                side, line = "over", float(market["floor_strike"])
            else:
                name = re.split(r" wins", market.get("yes_sub_title") or market["title"])[0]
                code = team_code(name)
                side = "home" if code == g["home"] else "away" if code == g["away"] else None
                if side is None:
                    continue
                line = -float(market["floor_strike"]) if kind == "spread" else None
            # Exchange quotes are supplementary: never treated as no-vig sportsbook votes.
            for is_yes in (True, False):
                if not is_yes and kind == "moneyline":
                    continue
                ask = float(market.get("yes_ask_dollars" if is_yes else "no_ask_dollars") or 0)
                bid = float(market.get("yes_bid_dollars" if is_yes else "no_bid_dollars") or 0)
                if not 0 < ask < 1:
                    continue
                actual_side = side if is_yes else {"home": "away", "away": "home", "over": "under"}[side]
                actual_line = line if is_yes or kind == "total" else -line
                output.append(quote(g, "kalshi", "Kalshi", kind, actual_side, actual_line, 1 / ask,
                                    market["observed_at"], ticker, kind="exchange", source_time=market.get("updated_time"),
                                    bid=bid, ask=ask, volume=market.get("volume_fp"), ticker=ticker,
                                    rules=market.get("rules_primary", "")))
        except (ValueError, TypeError, KeyError, IndexError):
            continue
    return output
