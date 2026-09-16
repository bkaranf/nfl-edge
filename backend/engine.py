"""Market-derived probability estimates, evidence gates, and all-in-cost EV."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import math
from statistics import median
from backend.domain import (
    EvaluationStatus,
    NetOutcomeReturns,
    Outcome,
    Pick,
    QuoteInput,
    ReasonCode,
    ReturnRequirement,
    age,
    canonical_line,
    cents,
    dt,
    iso,
    utcnow,
)
from backend.settlement_profiles import ProfileRegistry, resolve_profile


def _quote_rule_identity(value: dict) -> str:
    identity = (
        value.get("rule_profile"),
        value.get("rule_profile_id"),
        value.get("rule_version"),
        value.get("settlement_profile"),
    )
    return repr(identity)


def pairs(quotes: list[dict], pick: Pick, settings: dict, now: datetime) -> list[dict]:
    """Use complete same-observation pairs, with one vote per actual bookmaker."""
    grouped = defaultdict(dict)
    target = canonical_line(pick.market, pick.side, pick.line)
    sides = ("over", "under") if pick.market == "total" else ("home", "away")
    for q in quotes:
        try:
            if (q["game_id"] != pick.game_id or q["market"] != pick.market or q.get("kind") == "exchange"
                    or q.get("status") != "open" or q["side"] not in sides
                    or q.get("period", "full_game") != pick.period
                    or canonical_line(q["market"], q["side"], q["line"]) != target):
                continue
            seconds = age(q["observed_at"], now)
            if not 0 <= seconds <= 86400 or not math.isfinite(q["decimal_price"]) or q["decimal_price"] <= 1:
                continue
            period = q.get("period", "full_game")
            grouped[(q["book"].casefold(), q["source"], q["batch"], period,
                     _quote_rule_identity(q))][q["side"]] = q
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
               "period": a.get("period", "full_game"), "rule_identity": _quote_rule_identity(a),
               "prices": {s: group[s]["decimal_price"] for s in sides},
               "reason": None if eligible else "Upstream age unverified" if a["kind"] == "redistributed" else "Stale observation"}
        key = a["book"].casefold()
        prior = by_book.get(key)
        if prior is None or (eligible, dt(ref["observed_at"])) > (prior["eligible"], dt(prior["observed_at"])):
            by_book[key] = ref
    return sorted(by_book.values(), key=lambda r: r["book"])


def estimate(quotes: list[dict], pick: Pick, settings: dict, now: datetime) -> dict:
    integer = pick.market != "moneyline" and pick.line is not None and pick.line == int(pick.line)
    if not integer:
        refs = pairs(quotes, pick, settings, now)
    else:
        # Estimate strict win and win-or-push from matching same-book half-point pairs.
        direction = -1 if pick.market == "spread" or pick.side == "under" else 1
        strict = pick.model_copy(update={"line": pick.line + direction * .5})
        inclusive = pick.model_copy(update={"line": pick.line - direction * .5})
        lower = {r["book"]: r for r in pairs(quotes, strict, settings, now)}
        upper = {r["book"]: r for r in pairs(quotes, inclusive, settings, now)}
        refs = []
        for book in lower.keys() & upper.keys():
            a, b = lower[book], upper[book]
            if any(a.get(field) != b.get(field) for field in ("source", "kind", "period", "rule_identity")):
                continue
            if a["probability"] > b["probability"] + 1e-9:
                continue
            # Comparing observations far apart can manufacture a push probability.
            if abs((dt(a["observed_at"]) - dt(b["observed_at"])).total_seconds()) > settings["max_age_seconds"]:
                continue
            win_probability = a["probability"]
            inclusive_probability = b["probability"]
            push_probability = inclusive_probability - win_probability
            loss_probability = 1 - inclusive_probability
            if min(win_probability, push_probability, loss_probability) < -1e-9:
                continue
            refs.append({**a, "push_probability": push_probability,
                         "loss_probability": loss_probability,
                         "eligible": a["eligible"] and b["eligible"],
                         "age_seconds": max(a["age_seconds"], b["age_seconds"]),
                         "reason": a["reason"] or b["reason"], "adjacent_lines": [strict.line, inclusive.line],
                         "inclusive_probability": inclusive_probability, "decimal_price": None,
                         "outcome_probabilities": {
                             "win": win_probability,
                             "tie_or_push": push_probability,
                             "loss": loss_probability,
                         }})
    eligible = [r for r in refs if r["eligible"]]
    enough = len(eligible) >= settings["min_books"]
    chosen = eligible if enough else refs
    win = median(r["probability"] for r in chosen) if chosen else None
    if integer and chosen:
        inclusive = median(r["inclusive_probability"] for r in chosen)
        push = inclusive - win
        loss = 1 - inclusive
    elif chosen:
        inclusive = win
        push = 0.0
        loss = 1 - win
        for ref in refs:
            ref["push_probability"] = 0.0
            ref["loss_probability"] = 1 - ref["probability"]
            ref["outcome_probabilities"] = {
                "win": ref["probability"],
                "tie_or_push": 0.0,
                "loss": 1 - ref["probability"],
            }
    else:
        inclusive = push = loss = None
    if win is not None and (min(win, push, loss) < -1e-9 or abs(win + push + loss - 1) > 1e-9):
        win = push = loss = inclusive = None

    def spread(field: str) -> float | None:
        values = [r[field] for r in chosen]
        return (max(values) - min(values)) * 100 if values else None

    disagreement = {
        "win_pp": spread("probability"),
        "tie_or_push_pp": spread("push_probability"),
        "loss_pp": spread("loss_probability"),
    }
    return {"win": win, "push": push, "loss": loss, "win_or_push": inclusive,
            "integer": integer, "references": refs,
            "book_count": len(refs), "eligible_count": len(eligible), "enough": enough,
            "basis": "eligible references" if enough else "research references",
            "disagreement_pp": disagreement["win_pp"], "disagreement": disagreement}


def _decimal(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def scenario_returns(
    prob: dict,
    game: dict,
    outcome_returns: NetOutcomeReturns,
    settings: dict,
    *,
    tie_possible: bool | None = None,
) -> list[dict]:
    """Return bounded ordinary-completion scenarios using explicit net cash returns."""
    if prob["win"] is None or outcome_returns.loss is None:
        return []
    if prob["integer"] and outcome_returns.tie_or_push is None:
        return []

    moneyline = bool(prob.get("is_moneyline"))
    if moneyline:
        tie_possible = True if tie_possible is None else tie_possible
        if tie_possible and outcome_returns.tie_or_push is None:
            return []
        tie_max = _decimal(settings["tie_max_pct"]) / Decimal("100")
        ties = [Decimal("0"), tie_max] if tie_possible else [Decimal("0")]
    else:
        ties = [Decimal("0")]

    q = _decimal(prob["win"])
    win_return = outcome_returns.win
    tie_return = outcome_returns.tie_or_push
    loss_return = outcome_returns.loss
    stress_mass = _decimal(settings["stress_pp"]) / Decimal("100")
    scenarios = []
    for tie in sorted(set(ties)):
        if moneyline:
            win_probability = (Decimal("1") - tie) * q
            push_probability = tie
            loss_probability = (Decimal("1") - tie) * (Decimal("1") - q)
        else:
            win_probability = q
            push_probability = _decimal(prob["push"])
            loss_probability = _decimal(prob["loss"])
        probabilities = (win_probability, push_probability, loss_probability)
        if min(probabilities) < 0 or abs(sum(probabilities) - Decimal("1")) > Decimal("0.000000001"):
            return []

        effective_tie_return = tie_return if tie_return is not None else Decimal("0")
        expected_return = (
            win_probability * win_return
            + push_probability * effective_tie_return
            + loss_probability * loss_return
        )
        shifted = min(stress_mass, win_probability)
        stressed_win = win_probability - shifted
        stressed_loss = loss_probability + shifted
        stress_return = (
            stressed_win * win_return
            + push_probability * effective_tie_return
            + stressed_loss * loss_return
        )
        scenarios.append({
            "win_probability": float(win_probability),
            "tie_or_push_probability": float(push_probability),
            "push_probability": float(push_probability),
            "loss_probability": float(loss_probability),
            "expected_return": float(expected_return),
            "expected_return_exact": _decimal_text(expected_return),
            "stress_return": float(stress_return),
            "stress_return_exact": _decimal_text(stress_return),
            "net_outcome_returns": outcome_returns.model_dump(mode="json"),
        })
    return scenarios


def returns(
    prob: dict,
    game: dict,
    winning: Decimal | float | str,
    push_return: Decimal | float | str | None,
    settings: dict,
    losing_return: Decimal | float | str | None = None,
) -> list[dict]:
    """Compatibility wrapper; callers must now provide the loss return explicitly."""
    vector = NetOutcomeReturns(win=winning, tie_or_push=push_return, loss=losing_return)
    return scenario_returns(prob, game, vector, settings)


def stake_cap(settings: dict, bets: list[dict], game_id: str, mode: str) -> dict:
    bankroll = cents(settings["bankroll"])
    open_bets = [b for b in bets if b["status"] == "open" and b["quote"]["mode"] == mode]
    total_open = sum(cents(b["quote"]["total_cost"]) for b in open_bets)
    game_open = sum(cents(b["quote"]["total_cost"]) for b in open_bets if b["quote"]["game_id"] == game_id)
    def percentage_cap(setting: str) -> int:
        amount = Decimal(bankroll) * _decimal(settings[setting]) / Decimal("100")
        return int(amount.to_integral_value(rounding=ROUND_FLOOR))

    cap = max(0, min(percentage_cap("stake_pct"),
                     percentage_cap("game_cap_pct") - game_open,
                     percentage_cap("open_cap_pct") - total_open,
                     bankroll - total_open))
    return {"configured": bankroll > 0, "cap": cap / 100 if bankroll else None,
            "game_open": game_open / 100, "total_open": total_open / 100}


def _break_even_rows(cost: Decimal, returns_vector: NetOutcomeReturns, scenarios: list[dict]) -> list[dict]:
    rows = []
    win_return = returns_vector.win
    loss_return = returns_vector.loss
    if loss_return is None:
        return rows
    tie_return = returns_vector.tie_or_push or Decimal("0")
    denominator = win_return - loss_return
    for scenario in scenarios:
        push_probability = _decimal(scenario["tie_or_push_probability"])
        row = {"tie_or_push_probability": float(push_probability)}
        if denominator == 0:
            invariant_return = (
                push_probability * tie_return
                + (Decimal("1") - push_probability) * loss_return
            )
            if invariant_return == cost:
                reason = "NON_UNIQUE_BREAK_EVEN"
                feasible = True
                profitability = "NO_POSITIVE_EV_PROBABILITY"
            elif invariant_return > cost:
                reason = "NO_BREAK_EVEN_ALL_POSITIVE"
                feasible = False
                profitability = "ALL_FEASIBLE_WIN_PROBABILITIES"
            else:
                reason = "NO_BREAK_EVEN_NONE_POSITIVE"
                feasible = False
                profitability = "NO_POSITIVE_EV_PROBABILITY"
            row.update({"win_probability": None, "win_probability_exact": None,
                        "feasible": feasible, "reason": reason,
                        "positive_ev_when": profitability})
        else:
            threshold = (
                cost
                - push_probability * tie_return
                - (Decimal("1") - push_probability) * loss_return
            ) / denominator
            feasible = Decimal("0") <= threshold <= Decimal("1") - push_probability
            row.update({"win_probability": float(threshold),
                        "win_probability_exact": _decimal_text(threshold),
                        "feasible": feasible,
                        "reason": None if feasible else "THRESHOLD_OUT_OF_RANGE",
                        "positive_ev_when": (
                            "WIN_PROBABILITY_ABOVE_BREAK_EVEN"
                            if denominator > 0
                            else "WIN_PROBABILITY_BELOW_BREAK_EVEN"
                        )})
        rows.append(row)
    return rows


def _largest_inclusive_cent(value: Decimal) -> int:
    return int((value * 100).to_integral_value(rounding=ROUND_FLOOR))


def _largest_strict_cent(value: Decimal) -> int:
    return int((value * 100).to_integral_value(rounding=ROUND_CEILING)) - 1


def jsonable_context(value) -> str:
    """Stable-enough issue key for the bounded primitive contexts emitted here."""
    if isinstance(value, dict):
        return repr(sorted((key, jsonable_context(item)) for key, item in value.items()))
    if isinstance(value, list):
        return repr([jsonable_context(item) for item in value])
    return repr(value)


def evaluate(
    quote: QuoteInput,
    game: dict,
    quotes: list[dict],
    settings: dict,
    bets: list[dict],
    now: datetime | None = None,
    profiles: ProfileRegistry | None = None,
) -> dict:
    now = now or utcnow()
    pick = Pick(**quote.model_dump(include={"game_id", "market", "side", "line", "period"}))
    prob = estimate(quotes, pick, settings, now)
    prob["is_moneyline"] = quote.market == "moneyline"
    profile_result = resolve_profile(quote, game, profiles, as_of=now)
    issues: list[dict] = list(profile_result["issues"])

    def add_issue(code: ReasonCode, message: str, field: str | None = None, **context):
        issue = {"code": code.value, "message": message}
        if field:
            issue["field"] = field
        if context:
            issue["context"] = context
        key = (issue["code"], issue.get("field"), jsonable_context(issue.get("context")))
        existing = {(item["code"], item.get("field"), jsonable_context(item.get("context"))) for item in issues}
        if key not in existing:
            issues.append(issue)

    if game["status"] != "scheduled" or dt(game["start_time"]) <= now:
        add_issue(ReasonCode.EVENT_NOT_PREGAME, "Pregame only: this game has started or is unavailable.")
    if prob["win"] is None:
        if prob["integer"]:
            add_issue(ReasonCode.INTEGER_ADJACENT_PAIRS_MISSING,
                      "Missing compatible same-book adjacent half-point pairs for an integer diagnostic.")
        else:
            add_issue(ReasonCode.REFERENCE_PAIR_MISSING,
                      "No complete two-sided reference prices exist for this exact selection.")
    if not prob["enough"]:
        add_issue(
            ReasonCode.INSUFFICIENT_ELIGIBLE_REFERENCES,
            f"{prob['eligible_count']} of {settings['min_books']} required distinct fresh sportsbooks are eligible.",
            eligible_count=prob["eligible_count"],
            required_count=settings["min_books"],
        )
    if prob["disagreement_pp"] is not None and prob["disagreement_pp"] > settings["max_disagreement_pp"]:
        add_issue(ReasonCode.REFERENCE_DISAGREEMENT,
                  "Reference win probabilities disagree beyond the configured limit.")

    quote_age = age(iso(quote.observed_at), now)
    if quote_age < 0:
        add_issue(ReasonCode.QUOTE_TIMESTAMP_IN_FUTURE,
                  "The target quote observation time is in the future.", "observed_at")
    elif quote_age > settings["max_age_seconds"]:
        add_issue(ReasonCode.QUOTE_STALE,
                  "The target quote is older than the configured observation limit.", "observed_at")
    if not quote.fees_confirmed:
        add_issue(ReasonCode.FEES_UNCONFIRMED,
                  "Confirm that total cost and outcome returns include all applicable fees.")

    vector = quote.outcome_returns
    profile = profile_result["profile"]
    profile_compatible = profile_result["compatible"]
    if vector.loss is None:
        add_issue(ReasonCode.OUTCOME_RETURN_REQUIRED,
                  "Enter the total net return for a loss; it is never inferred as zero.",
                  "outcome_returns.loss", outcome="loss")

    tie_rule = profile.outcome_rules[Outcome.TIE_OR_PUSH] if profile and profile_compatible else None
    if quote.market == "moneyline" or prob["integer"]:
        if tie_rule is None or tie_rule.requirement == ReturnRequirement.REQUIRED:
            if vector.tie_or_push is None:
                add_issue(ReasonCode.OUTCOME_RETURN_REQUIRED,
                          "Enter the total net return for a tie or push; it is never derived from the win return.",
                          "outcome_returns.tie_or_push", outcome="tie_or_push")
    elif vector.tie_or_push is not None and tie_rule is None:
        add_issue(ReasonCode.SETTLEMENT_PROFILE_CONTRADICTION,
                  "A half-point ordinary-completion calculation has no tie or push outcome.",
                  "outcome_returns.tie_or_push", outcome="tie_or_push")

    if prob["integer"]:
        add_issue(ReasonCode.INTEGER_LINE_RESEARCH_ONLY,
                  "Integer-line calculations are diagnostic and cannot meet the v0.2 screen.")

    blocking_codes = {
        ReasonCode.SETTLEMENT_PROFILE_CONTRADICTION.value,
        ReasonCode.OUTCOME_RETURN_REQUIRED.value,
    }
    financial_inputs_valid = not any(item["code"] in blocking_codes for item in issues)
    tie_possible = None
    if quote.market == "moneyline" and tie_rule is not None:
        tie_possible = tie_rule.requirement == ReturnRequirement.REQUIRED
    scenarios = scenario_returns(prob, game, vector, settings, tie_possible=tie_possible) if financial_inputs_valid else []

    if prob["integer"] and vector.loss is not None and vector.tie_or_push is not None:
        payoff_rows = []
        for ref in prob["references"]:
            probabilities = ref.get("outcome_probabilities")
            if not probabilities:
                continue
            value = (
                _decimal(probabilities["win"]) * vector.win
                + _decimal(probabilities["tie_or_push"]) * vector.tie_or_push
                + _decimal(probabilities["loss"]) * vector.loss
            )
            payoff_rows.append({"book": ref["book"], "expected_return": float(value),
                                "expected_return_exact": _decimal_text(value)})
        prob["payoff_returns"] = payoff_rows
        if payoff_rows:
            values = [_decimal(row["expected_return_exact"]) for row in payoff_rows]
            payoff_spread = max(values) - min(values)
            prob["disagreement"]["payoff_return"] = float(payoff_spread)
            prob["disagreement"]["payoff_return_exact"] = _decimal_text(payoff_spread)

    net = None
    if scenarios:
        cost = quote.total_cost
        low = min(_decimal(item["expected_return_exact"]) for item in scenarios)
        high = max(_decimal(item["expected_return_exact"]) for item in scenarios)
        stressed = min(_decimal(item["stress_return_exact"]) for item in scenarios)
        roi = (low / cost - Decimal("1")) * Decimal("100")
        roi_high = (high / cost - Decimal("1")) * Decimal("100")
        stress_roi = (stressed / cost - Decimal("1")) * Decimal("100")
        if roi < _decimal(settings["min_roi_pct"]):
            add_issue(ReasonCode.ROI_BELOW_MINIMUM,
                      f"Conservative estimated ROI is below {settings['min_roi_pct']:g}%.")
        if stress_roi <= 0:
            add_issue(ReasonCode.STRESSED_ROI_NOT_POSITIVE,
                      "Estimated ROI is not positive after the probability stress test.")

        roi_denominator = Decimal("1") + _decimal(settings["min_roi_pct"]) / Decimal("100")
        roi_cents = _largest_inclusive_cent(low / roi_denominator)
        stress_cents = _largest_strict_cent(stressed)
        max_cost_cents = max(0, min(roi_cents, stress_cents))
        max_cost = Decimal(max_cost_cents) / Decimal("100")
        break_even = _break_even_rows(cost, vector, scenarios)
        legacy_break_even = (
            break_even[0]["win_probability"]
            if len(break_even) == 1 and break_even[0]["feasible"]
            else None
        )
        ev = low - cost
        net = {
            "ev": round(float(ev), 4),
            "ev_exact": _decimal_text(ev),
            "roi_pct": float(roi),
            "roi_pct_exact": _decimal_text(roi),
            "roi_high_pct": float(roi_high),
            "stress_roi_pct": float(stress_roi),
            "stress_roi_pct_exact": _decimal_text(stress_roi),
            "max_cost": float(max_cost),
            "max_cost_exact": f"{max_cost:.2f}",
            "break_even_probability": legacy_break_even,
            "break_even": break_even,
            "scenarios": scenarios,
        }

    insufficient_codes = {
        ReasonCode.REFERENCE_PAIR_MISSING.value,
        ReasonCode.INTEGER_ADJACENT_PAIRS_MISSING.value,
        ReasonCode.OUTCOME_RETURN_REQUIRED.value,
        ReasonCode.SETTLEMENT_PROFILE_CONTRADICTION.value,
    }
    if net is None or any(item["code"] in insufficient_codes for item in issues):
        status = EvaluationStatus.INSUFFICIENT_DATA
    elif issues:
        status = EvaluationStatus.RESEARCH_ONLY
    else:
        status = EvaluationStatus.MEETS_ESTIMATED_SCREEN
    labels = {
        EvaluationStatus.INSUFFICIENT_DATA: "Insufficient data",
        EvaluationStatus.RESEARCH_ONLY: "Research only",
        EvaluationStatus.MEETS_ESTIMATED_SCREEN: "Meets estimated EV screen",
        EvaluationStatus.EXPIRED: "Expired",
    }
    qualified = status == EvaluationStatus.MEETS_ESTIMATED_SCREEN
    sizing = stake_cap(settings, bets, quote.game_id, quote.mode)
    within_cap = sizing["configured"] and cents(quote.total_cost) <= cents(sizing["cap"])
    exact_money = quote.original_monetary_strings
    calculation = {
        "version": "ev-v2",
        "original_monetary_strings": exact_money,
        "net_outcome_returns": vector.model_dump(mode="json"),
        "settlement_profile": {
            "requested": profile_result["requested"],
            "resolved": profile_result["snapshot"],
            "compatible": profile_result["compatible"],
            "admitted": profile_result["admitted"],
        },
        "conditional_on_ordinary_completion": True if profile is None else profile.conditional_on_ordinary_completion,
    }
    assumptions = "Market median; proportional margin removal. Explicit net outcome returns; EV is conditional on ordinary completion."
    if quote.market == "moneyline":
        assumptions += f" Tie sensitivity spans 0–{settings['tie_max_pct']:g}% when a tie outcome applies."
    elif prob["integer"]:
        assumptions += " Integer push probability is a research diagnostic from coherent same-book adjacent vectors."
    else:
        assumptions += " The half-point ordinary-completion model has win and loss outcomes."
    reason_codes = list(dict.fromkeys(item["code"] for item in issues))
    return {
        "evaluated_at": iso(now),
        "status": status.value,
        "qualified": qualified,
        "label": labels[status],
        "reason_codes": reason_codes,
        "reasons": [item["message"] for item in issues],
        "issues": issues,
        "probability": prob,
        "net": net,
        "calculation": calculation,
        "sizing": sizing,
        "within_cap": within_cap,
        "quote_age_seconds": round(quote_age),
        "settings": settings,
        "assumptions": assumptions,
    }


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
