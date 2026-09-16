"""Market-derived probability estimates, evidence gates, and all-in-cost EV."""
from collections import defaultdict
from datetime import datetime
import math
from statistics import median

from backend.domain import Pick, QuoteInput, age, canonical_line, cents, dt, iso, utcnow


def pairs(quotes: list[dict], pick: Pick, settings: dict, now: datetime) -> list[dict]:
    """Use complete same-observation pairs, with one vote per actual bookmaker."""
    grouped = defaultdict(dict)
    target = canonical_line(pick.market, pick.side, pick.line)
    sides = ("over", "under") if pick.market == "total" else ("home", "away")
    for q in quotes:
        try:
            if (q["game_id"] != pick.game_id or q["market"] != pick.market or q.get("kind") == "exchange"
                    or q.get("status") != "open" or q["side"] not in sides
                    or canonical_line(q["market"], q["side"], q["line"]) != target):
                continue
            seconds = age(q["observed_at"], now)
            if not 0 <= seconds <= 86400 or not math.isfinite(q["decimal_price"]) or q["decimal_price"] <= 1:
                continue
            grouped[(q["book"].casefold(), q["source"], q["batch"])][q["side"]] = q
        except (KeyError, TypeError, ValueError):
            continue
    by_book = {}
    for group in grouped.values():
        if not all(s in group for s in sides):
            continue
        a, b = [group[s] for s in sides]
        # Providers must emit both sides from one observation, never mix open/close prices.
        if a["observed_at"] != b["observed_at"]:
            continue
        mass = 1 / a["decimal_price"] + 1 / b["decimal_price"]
        seconds = age(a["observed_at"], now)
        eligible = (seconds <= settings["max_age_seconds"]
                    and all(q.get("kind") in ("direct", "manual") for q in (a, b)))
        ref = {"book": a["book"], "source": a["source"], "kind": a["kind"],
               "observed_at": a["observed_at"], "age_seconds": round(seconds), "eligible": eligible,
               "probability": (1 / group[pick.side]["decimal_price"]) / mass,
               "decimal_price": group[pick.side]["decimal_price"], "overround_pct": (mass - 1) * 100,
               "prices": {s: group[s]["decimal_price"] for s in sides},
               "reason": None if eligible else "Upstream age unverified" if a["kind"] == "redistributed" else "Stale observation"}
        key = a["book"].casefold()
        prior = by_book.get(key)
        if prior is None or (eligible, dt(ref["observed_at"])) > (prior["eligible"], dt(prior["observed_at"])):
            by_book[key] = ref
    return sorted(by_book.values(), key=lambda r: r["book"])


def estimate(quotes: list[dict], pick: Pick, settings: dict, now: datetime) -> dict:
    integer = pick.market != "moneyline" and pick.line == int(pick.line)
    if not integer:
        refs = pairs(quotes, pick, settings, now)
    else:
        # Estimate strict win and win-or-push from matching half-point pairs.
        direction = -1 if pick.market == "spread" or pick.side == "under" else 1
        strict = pick.model_copy(update={"line": pick.line + direction * .5})
        inclusive = pick.model_copy(update={"line": pick.line - direction * .5})
        lower = {r["book"]: r for r in pairs(quotes, strict, settings, now)}
        upper = {r["book"]: r for r in pairs(quotes, inclusive, settings, now)}
        refs = []
        for book in lower.keys() & upper.keys():
            a, b = lower[book], upper[book]
            if a["probability"] > b["probability"] + 1e-9:
                continue
            # Comparing observations far apart can manufacture a push probability.
            if abs((dt(a["observed_at"]) - dt(b["observed_at"])).total_seconds()) > settings["max_age_seconds"]:
                continue
            refs.append({**a, "push_probability": b["probability"] - a["probability"],
                         "eligible": a["eligible"] and b["eligible"],
                         "age_seconds": max(a["age_seconds"], b["age_seconds"]),
                         "reason": a["reason"] or b["reason"], "adjacent_lines": [strict.line, inclusive.line],
                         "inclusive_probability": b["probability"], "decimal_price": None})
    eligible = [r for r in refs if r["eligible"]]
    enough = len(eligible) >= settings["min_books"]
    chosen = eligible if enough else refs
    win = median(r["probability"] for r in chosen) if chosen else None
    push = median(r.get("push_probability", 0) for r in chosen) if chosen else None
    if win is not None and win + push > 1 + 1e-9:
        win, push = None, None
    return {"win": win, "push": push, "integer": integer, "references": refs,
            "book_count": len(refs), "eligible_count": len(eligible), "enough": enough,
            "basis": "eligible references" if enough else "research references",
            "disagreement_pp": (max(r["probability"] for r in chosen) - min(r["probability"] for r in chosen)) * 100 if chosen else None}


def returns(prob: dict, game: dict, winning: float, push_return: float | None, settings: dict) -> list[dict]:
    if prob["win"] is None or (prob["integer"] and push_return is None):
        return []
    q = prob["win"]
    scenarios = []
    ties = [0, float(settings["tie_max_pct"]) / 100] if game.get("season_type") != "POST" and prob.get("is_moneyline") else [0]
    for tie in sorted(set(ties)):
        w = (1 - tie) * q
        p = tie if prob.get("is_moneyline") else prob["push"]
        payout_on_push = winning / 2 if prob.get("is_moneyline") else (push_return or 0)
        expected_return = w * winning + p * payout_on_push
        stress_return = max(0, w - settings["stress_pp"] / 100) * winning + p * payout_on_push
        scenarios.append({"win_probability": w, "push_probability": p, "loss_probability": max(0, 1-w-p),
                          "expected_return": expected_return, "stress_return": stress_return})
    return scenarios


def stake_cap(settings: dict, bets: list[dict], game_id: str, mode: str) -> dict:
    bankroll = cents(settings["bankroll"])
    open_bets = [b for b in bets if b["status"] == "open" and b["quote"]["mode"] == mode]
    total_open = sum(cents(b["quote"]["total_cost"]) for b in open_bets)
    game_open = sum(cents(b["quote"]["total_cost"]) for b in open_bets if b["quote"]["game_id"] == game_id)
    cap = max(0, min(int(bankroll * settings["stake_pct"] / 100),
                     int(bankroll * settings["game_cap_pct"] / 100) - game_open,
                     int(bankroll * settings["open_cap_pct"] / 100) - total_open,
                     bankroll - total_open))
    return {"configured": bankroll > 0, "cap": cap / 100 if bankroll else None,
            "game_open": game_open / 100, "total_open": total_open / 100}


def evaluate(quote: QuoteInput, game: dict, quotes: list[dict], settings: dict, bets: list[dict], now: datetime | None = None) -> dict:
    now = now or utcnow()
    pick = Pick(**quote.model_dump(include={"game_id", "market", "side", "line"}))
    prob = estimate(quotes, pick, settings, now)
    prob["is_moneyline"] = quote.market == "moneyline"
    reasons = []
    if game["status"] != "scheduled" or dt(game["start_time"]) <= now:
        reasons.append("Pregame only: this game has started or is unavailable.")
    if prob["win"] is None:
        reasons.append("Missing matched adjacent half-point pairs to estimate a push." if prob["integer"] else "No complete two-sided reference prices for this exact selection.")
    if not prob["enough"]:
        reasons.append(f"{prob['eligible_count']} of {settings['min_books']} required distinct fresh sportsbooks; redistributed prices have unverified upstream age.")
    if prob["disagreement_pp"] is not None and prob["disagreement_pp"] > settings["max_disagreement_pp"]:
        reasons.append("Reference probabilities disagree beyond the configured limit.")
    quote_age = age(iso(quote.observed_at), now)
    if not 0 <= quote_age <= settings["max_age_seconds"]:
        reasons.append("Underdog quote is stale or its timestamp is in the future.")
    if not quote.fees_confirmed:
        reasons.append("Confirm the total cost includes all entry fees.")
    if not quote.rules_confirmed or quote.exchange == "Unknown":
        reasons.append("Identify the exchange and confirm the displayed settlement rules.")
    if prob["integer"] and quote.push_return is None:
        reasons.append("Enter the total amount returned if this integer line pushes.")
    cost, winning = float(quote.total_cost), float(quote.winning_payout)
    scenarios = returns(prob, game, winning, float(quote.push_return) if quote.push_return is not None else None, settings)
    net = None
    if scenarios:
        low = min(s["expected_return"] for s in scenarios)
        high = max(s["expected_return"] for s in scenarios)
        stressed = min(s["stress_return"] for s in scenarios)
        roi, stress = (low / cost - 1) * 100, (stressed / cost - 1) * 100
        if roi + 1e-9 < settings["min_roi_pct"]:
            reasons.append(f"Conservative estimated ROI is below {settings['min_roi_pct']:g}%.")
        if stress <= 0:
            reasons.append("Estimated ROI is not positive after the probability stress test.")
        # A strictly positive stress edge must survive cent rounding at the price ceiling.
        ceiling = min(low / (1 + settings["min_roi_pct"] / 100), stressed - 1e-9)
        net = {"ev": round(low-cost, 4), "roi_pct": roi, "roi_high_pct": (high/cost-1)*100,
               "stress_roi_pct": stress, "max_cost": max(0, math.floor((ceiling + 1e-10)*100)/100),
               "break_even_probability": cost/winning, "scenarios": scenarios}
    sizing = stake_cap(settings, bets, quote.game_id, quote.mode)
    within_cap = sizing["configured"] and cents(quote.total_cost) <= cents(sizing["cap"])
    return {"evaluated_at": iso(now), "qualified": not reasons and net is not None,
            "label": "Meets estimated EV screen" if not reasons and net else "Research only",
            "reasons": reasons, "probability": prob, "net": net, "sizing": sizing, "within_cap": within_cap,
            "quote_age_seconds": round(quote_age), "settings": settings,
            "assumptions": "Market median; proportional margin removal. Losing return $0. " +
            (f"Regular-season ties stressed from 0–{settings['tie_max_pct']:g}%; tie pays half the winning return." if quote.market == "moneyline" and game.get("season_type") != "POST" else
             "Push probability from adjacent half-points." if prob["integer"] else "Full game including overtime; no tie/push outcome.")}


def make_board(games: dict, quotes: list[dict], settings: dict, now: datetime | None = None) -> list[dict]:
    now = now or utcnow()
    rows = []
    for g in sorted(games.values(), key=lambda g: g["start_time"]):
        if g["status"] != "scheduled" or not 0 < (dt(g["start_time"]) - now).total_seconds() <= 14 * 86400:
            continue
        g_quotes = [q for q in quotes if q["game_id"] == g["id"]]
        for market in ("moneyline", "spread", "total"):
            # Display the most supported exact line; the checker allows another exact line.
            candidates = {canonical_line(market, q["side"], q["line"]) for q in g_quotes if q["market"] == market and q.get("kind") != "exchange" and q.get("main", True)}
            if not candidates:
                candidates = {None} if market == "moneyline" else set()
            scored = []
            for line in candidates:
                pick = Pick(game_id=g["id"], market=market, side="over" if market == "total" else "home", line=line)
                refs = pairs(g_quotes, pick, settings, now)
                scored.append((len(refs), sum(r["eligible"] for r in refs), -sum(r["age_seconds"] for r in refs), line))
            if not scored:
                continue
            line = max(scored, key=lambda x: x[:3])[3]
            for side in (("over", "under") if market == "total" else ("away", "home")):
                selected_line = -line if market == "spread" and side == "away" else line
                pick = Pick(game_id=g["id"], market=market, side=side, line=selected_line)
                evidence = estimate(g_quotes, pick, settings, now)
                raw = pairs(g_quotes, pick, settings, now)
                exchange = [q for q in g_quotes if q["market"] == market and q["side"] == side and q["line"] == selected_line and q.get("kind") == "exchange"]
                rows.append({**pick.model_dump(), "game": g, "references": raw,
                             "probability": evidence["win"], "eligible_count": evidence["eligible_count"],
                             "book_count": evidence["book_count"], "exchange_quotes": exchange[:3]})
    return rows
