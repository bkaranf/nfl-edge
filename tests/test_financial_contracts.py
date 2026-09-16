from datetime import timedelta

import pytest

from backend.domain import (
    NetOutcomeReturns,
    Outcome,
    OutcomeReturnRule,
    Pick,
    ProfileAdmission,
    QuoteInput,
    ReturnRequirement,
    american_to_decimal,
)
from backend.engine import evaluate, pairs, stake_cap
from backend.providers import quote
from backend.settlement_profiles import PROFILE_REGISTRY, build_profile, build_registry, list_profiles
from tests.test_engine import (
    GAME,
    HALF_TOTAL_PROFILE,
    INTEGER_SPREAD_PROFILE,
    INTEGER_TOTAL_PROFILE,
    MONEYLINE_PROFILE,
    NOW,
    SETTINGS,
    input_quote,
    pair,
    profile_ref,
    references,
    registry,
)


def test_production_registry_has_no_admitted_or_user_selectable_profile():
    assert PROFILE_REGISTRY == {}
    assert list_profiles(admitted_only=True) == []


def test_duplicate_profile_version_with_different_content_is_invalid():
    fields = HALF_TOTAL_PROFILE.model_dump(exclude={"content_hash"})
    conflicting = build_profile(**{**fields, "product": "different-test-product"})
    with pytest.raises(ValueError, match="conflicting content"):
        build_registry((HALF_TOTAL_PROFILE, conflicting))


def profile_variant(profile, **updates):
    fields = profile.model_dump(exclude={"content_hash"})
    return build_profile(**{**fields, **updates})


def test_canonical_returns_bridge_legacy_fields_exactly_and_rejects_disagreement():
    quote_input = QuoteInput(
        game_id=GAME["id"], market="total", side="over", line=44.5,
        total_cost="10.50", observed_at=NOW, exchange="Kalshi",
        outcome_returns={"win": "20.00", "tie_or_push": None, "loss": "0.00"},
    )
    assert quote_input.winning_payout.as_tuple().exponent == -2
    assert quote_input.winning_payout == quote_input.outcome_returns.win
    assert quote_input.losing_return == quote_input.outcome_returns.loss
    with pytest.raises(ValueError, match="OUTCOME_RETURN_CONTRADICTION"):
        QuoteInput(
            game_id=GAME["id"], market="total", side="over", line=44.5,
            total_cost="10.50", winning_payout="21.00", losing_return="0.00",
            observed_at=NOW, exchange="Kalshi",
            outcome_returns={"win": "20.00", "tie_or_push": None, "loss": "0.00"},
        )


@pytest.mark.parametrize(
    "updates,missing_field",
    [
        ({"losing_return": None}, "outcome_returns.loss"),
        ({"market": "moneyline", "side": "home", "line": None, "push_return": None},
         "outcome_returns.tie_or_push"),
    ],
)
def test_missing_required_returns_never_become_zero_or_half_win(updates, missing_field):
    profile = MONEYLINE_PROFILE if updates.get("market") == "moneyline" else HALF_TOTAL_PROFILE
    quote_input = input_quote(settlement_profile=profile_ref(profile), **updates)
    result = evaluate(quote_input, GAME, references(market=quote_input.market, line=quote_input.line),
                      SETTINGS, [], NOW, registry(profile))
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["net"] is None
    assert any(issue.get("field") == missing_field for issue in result["issues"])
    assert "OUTCOME_RETURN_REQUIRED" in result["reason_codes"]


def test_unsupported_complete_quote_keeps_diagnostic_but_never_passes():
    result = evaluate(input_quote(), GAME, references(), SETTINGS, [], NOW)
    assert result["net"]["ev"] == pytest.approx(2)
    assert result["status"] == "RESEARCH_ONLY"
    assert result["reason_codes"] == ["SETTLEMENT_PROFILE_REQUIRED"]
    assert result["qualified"] is False
    assert result["qualified"] == (result["status"] == "MEETS_ESTIMATED_SCREEN")


def test_synthetic_admitted_half_point_profile_can_exercise_screen_path():
    quote_input = input_quote(
        total_cost="10.50", winning_payout="20.00", losing_return="0.00",
        settlement_profile=profile_ref(HALF_TOTAL_PROFILE),
    )
    result = evaluate(quote_input, GAME, references(probability=.55), SETTINGS, [], NOW,
                      registry(HALF_TOTAL_PROFILE))
    assert result["status"] == "MEETS_ESTIMATED_SCREEN"
    assert result["qualified"]
    assert result["net"]["ev"] == pytest.approx(.50)
    assert result["net"]["stress_roi_pct"] == pytest.approx(.1 / 10.5 * 100)
    assert result["calculation"]["version"] == "ev-v2"
    assert result["calculation"]["original_monetary_strings"] == {
        "total_cost": "10.50", "winning_payout": "20.00",
        "push_return": None, "losing_return": "0.00",
        "outcome_returns": {"win": None, "tie_or_push": None, "loss": None},
    }
    snapshot = result["calculation"]["settlement_profile"]["resolved"]
    assert snapshot["content_hash"].startswith("sha256:")
    assert snapshot["admission"] == "ADMITTED"
    assert snapshot["outcome_rules"]["loss"] == {"requirement": "REQUIRED", "exact": "0"}
    assert snapshot["evidence_ids"] == ["synthetic:test-only"]
    assert snapshot["overtime_included"] is True


def test_profile_must_be_admitted_and_effective_at_evaluation_time():
    future_admission = profile_variant(HALF_TOTAL_PROFILE, admitted_at=NOW + timedelta(seconds=1))
    quote_input = input_quote(settlement_profile=profile_ref(future_admission))
    result = evaluate(quote_input, GAME, references(), SETTINGS, [], NOW, registry(future_admission))
    assert result["net"] is not None
    assert result["status"] == "RESEARCH_ONLY"
    assert "SETTLEMENT_PROFILE_NOT_ADMITTED" in result["reason_codes"]
    assert result["calculation"]["settlement_profile"]["admitted"] is False

    expires_after_observation = profile_variant(
        HALF_TOTAL_PROFILE, effective_to=NOW + timedelta(seconds=30)
    )
    quote_input = input_quote(settlement_profile=profile_ref(expires_after_observation))
    result = evaluate(
        quote_input, GAME, references(), SETTINGS, [], NOW + timedelta(seconds=60),
        registry(expires_after_observation),
    )
    assert result["net"] is not None
    assert result["status"] == "RESEARCH_ONLY"
    assert "SETTLEMENT_PROFILE_NOT_EFFECTIVE" in result["reason_codes"]
    assert result["calculation"]["settlement_profile"]["admitted"] is False


def test_profile_hash_detects_nested_rule_mutation_and_reason_codes_are_unique():
    tampered = HALF_TOTAL_PROFILE.model_copy(deep=True)
    tampered.outcome_rules[Outcome.LOSS] = OutcomeReturnRule(
        requirement=ReturnRequirement.REQUIRED, exact="1"
    )
    quote_input = input_quote(settlement_profile=profile_ref(tampered))
    result = evaluate(quote_input, GAME, references(), SETTINGS, [], NOW, registry(tampered))
    assert result["net"] is None
    assert result["reason_codes"].count("SETTLEMENT_PROFILE_CONTRADICTION") == 1
    assert len(result["reason_codes"]) == len(set(result["reason_codes"]))


def test_unsupported_overtime_and_tie_semantics_cannot_pass():
    no_overtime = profile_variant(HALF_TOTAL_PROFILE, overtime_included=False)
    quote_input = input_quote(settlement_profile=profile_ref(no_overtime))
    result = evaluate(quote_input, GAME, references(), SETTINGS, [], NOW, registry(no_overtime))
    assert result["net"] is None
    assert "SETTLEMENT_PROFILE_CONTRADICTION" in result["reason_codes"]

    forbidden_regular_tie = profile_variant(
        MONEYLINE_PROFILE,
        outcome_rules={
            Outcome.WIN: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED),
            Outcome.TIE_OR_PUSH: OutcomeReturnRule(requirement=ReturnRequirement.FORBIDDEN),
            Outcome.LOSS: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED, exact="0"),
        },
    )
    quote_input = input_quote(
        market="moneyline", side="home", line=None, push_return=None,
        settlement_profile=profile_ref(forbidden_regular_tie),
    )
    result = evaluate(
        quote_input, GAME, references(market="moneyline", line=None), SETTINGS, [], NOW,
        registry(forbidden_regular_tie),
    )
    assert result["net"] is None
    assert "SETTLEMENT_PROFILE_CONTRADICTION" in result["reason_codes"]

    required_half_point_tie = profile_variant(
        HALF_TOTAL_PROFILE,
        outcome_rules={
            Outcome.WIN: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED),
            Outcome.TIE_OR_PUSH: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED),
            Outcome.LOSS: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED, exact="0"),
        },
    )
    quote_input = input_quote(
        push_return="0", settlement_profile=profile_ref(required_half_point_tie)
    )
    result = evaluate(
        quote_input, GAME, references(), SETTINGS, [], NOW, registry(required_half_point_tie)
    )
    assert result["net"] is None
    assert "SETTLEMENT_PROFILE_CONTRADICTION" in result["reason_codes"]


def test_fair_coin_and_strict_cent_ceiling_hand_calculations():
    fair = input_quote(total_cost="115", winning_payout="215", losing_return="0")
    fair_result = evaluate(fair, GAME, references(probability=.5), SETTINGS, [], NOW)
    assert fair_result["net"]["ev"] == pytest.approx(-7.5)
    assert fair_result["net"]["roi_pct"] == pytest.approx(-6.52173913)

    profiles = registry(HALF_TOTAL_PROFILE)
    base = input_quote(settlement_profile=profile_ref(HALF_TOTAL_PROFILE))
    result = evaluate(base, GAME, references(probability=.5), SETTINGS, [], NOW, profiles)
    assert result["net"]["max_cost_exact"] == "9.59"
    at_ceiling = evaluate(base.model_copy(update={"total_cost": base.total_cost.__class__("9.59")}),
                          GAME, references(probability=.5), SETTINGS, [], NOW, profiles)
    next_cent = evaluate(base.model_copy(update={"total_cost": base.total_cost.__class__("9.60")}),
                         GAME, references(probability=.5), SETTINGS, [], NOW, profiles)
    assert at_ceiling["qualified"]
    assert not next_cent["qualified"]
    assert "STRESSED_ROI_NOT_POSITIVE" in next_cent["reason_codes"]


def test_nonzero_overround_pair_normalizes_to_twelve_over_twenty_three():
    observed = NOW.isoformat()
    batch = "overround"
    quotes = [
        quote(GAME, "fixture", "Bovada", "moneyline", "home", None,
              american_to_decimal(-120), observed, batch, kind="manual"),
        quote(GAME, "fixture", "Bovada", "moneyline", "away", None,
              american_to_decimal(100), observed, batch, kind="manual"),
    ]
    selection = Pick(game_id=GAME["id"], market="moneyline", side="home", line=None)
    assert pairs(quotes, selection, SETTINGS, NOW)[0]["probability"] == pytest.approx(12 / 23)


def test_financial_pairs_reject_period_and_rule_semantic_mismatches():
    selection = Pick(game_id=GAME["id"], market="total", side="over", line=44.5)
    mismatched_period = pair(line=44.5)
    mismatched_period[0]["period"] = "first_half"
    assert pairs(mismatched_period, selection, SETTINGS, NOW) == []

    mismatched_rule = pair(line=44.5)
    mismatched_rule[0]["rule_profile_id"] = "rule-a"
    mismatched_rule[1]["rule_profile_id"] = "rule-b"
    assert pairs(mismatched_rule, selection, SETTINGS, NOW) == []


def test_explicit_zero_moneyline_tie_return_is_used_not_half_win():
    quote_input = input_quote(
        market="moneyline", side="home", line=None,
        total_cost="70.60", winning_payout="100.00", push_return="0.00", losing_return="0.00",
        settlement_profile=profile_ref(MONEYLINE_PROFILE),
    )
    result = evaluate(
        quote_input, GAME, references(market="moneyline", line=None, probability=.74),
        SETTINGS, [], NOW, registry(MONEYLINE_PROFILE),
    )
    worst = min(result["net"]["scenarios"], key=lambda scenario: scenario["expected_return"])
    assert (worst["win_probability"], worst["tie_or_push_probability"], worst["loss_probability"]) == pytest.approx((.703, .05, .247))
    assert worst["expected_return"] == pytest.approx(70.30)
    assert result["net"]["ev"] == pytest.approx(-.30)
    assert not result["qualified"]


def test_profile_return_contradiction_has_no_net_but_remains_a_valid_quote_record():
    profile = build_profile(
        profile_id="test.synthetic.moneyline-exact-tie", version=1,
        exchange="Kalshi", product="synthetic-test-only", market="moneyline",
        season_types=("REG",), overtime_included=True,
        outcome_rules={
            Outcome.WIN: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED),
            Outcome.TIE_OR_PUSH: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED, exact="50.00"),
            Outcome.LOSS: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED, exact="0.00"),
        },
        evidence_ids=("synthetic:test-only",), effective_from=NOW-timedelta(days=1),
        admission=ProfileAdmission.ADMITTED, admitted_at=NOW-timedelta(days=1),
        decision_id="synthetic-test-only",
    )
    quote_input = input_quote(
        market="moneyline", side="home", line=None, push_return="0.00",
        settlement_profile=profile_ref(profile),
    )
    result = evaluate(quote_input, GAME, references(market="moneyline", line=None),
                      SETTINGS, [], NOW, registry(profile))
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["net"] is None
    assert "SETTLEMENT_PROFILE_CONTRADICTION" in result["reason_codes"]
    assert quote_input.outcome_returns.tie_or_push == 0  # explicit economics remain intact for journaling


def test_profile_revision_exchange_market_and_period_mismatches_never_pass():
    unknown_revision = input_quote(settlement_profile={
        "profile_id": HALF_TOTAL_PROFILE.profile_id, "version": HALF_TOTAL_PROFILE.version + 1,
    })
    unknown = evaluate(unknown_revision, GAME, references(), SETTINGS, [], NOW,
                       registry(HALF_TOTAL_PROFILE))
    assert unknown["status"] == "RESEARCH_ONLY"
    assert "SETTLEMENT_PROFILE_UNKNOWN" in unknown["reason_codes"]

    wrong_exchange = input_quote(
        exchange="Unknown", settlement_profile=profile_ref(HALF_TOTAL_PROFILE)
    )
    mismatch = evaluate(wrong_exchange, GAME, references(), SETTINGS, [], NOW,
                        registry(HALF_TOTAL_PROFILE))
    assert mismatch["net"] is None
    assert "SETTLEMENT_PROFILE_CONTRADICTION" in mismatch["reason_codes"]

    wrong_market = input_quote(settlement_profile=profile_ref(MONEYLINE_PROFILE))
    mismatch = evaluate(wrong_market, GAME, references(), SETTINGS, [], NOW,
                        registry(MONEYLINE_PROFILE))
    assert mismatch["net"] is None
    assert not mismatch["qualified"]

    with pytest.raises(ValueError):
        input_quote(period="first_half")


@pytest.mark.parametrize(
    "market,side,line,strict_line,inclusive_line,strict_base,inclusive_base",
    [
        ("total", "over", 44, 44.5, 43.5, .4, .5),
        ("total", "under", 44, 43.5, 44.5, .6, .5),
        ("spread", "home", -3, -3.5, -2.5, .4, .5),
        ("spread", "home", 3, 2.5, 3.5, .4, .5),
        ("spread", "home", 0, -.5, .5, .4, .5),
        ("spread", "away", 3, -2.5, -3.5, .6, .5),
        ("spread", "away", -3, 3.5, 2.5, .6, .5),
        ("spread", "away", 0, .5, -.5, .6, .5),
    ],
)
def test_all_integer_directions_are_coherent_symmetric_and_never_pass(
    market, side, line, strict_line, inclusive_line, strict_base, inclusive_base
):
    profile = INTEGER_TOTAL_PROFILE if market == "total" else INTEGER_SPREAD_PROFILE
    quotes = references(market=market, line=strict_line, probability=strict_base)
    quotes += references(market=market, line=inclusive_line, probability=inclusive_base)
    quote_input = input_quote(
        market=market, side=side, line=line, push_return="8",
        settlement_profile=profile_ref(profile),
    )
    result = evaluate(quote_input, GAME, quotes, SETTINGS, [], NOW, registry(profile))
    vector = result["probability"]
    assert (vector["win"], vector["push"], vector["loss"]) == pytest.approx((.4, .1, .5))
    assert vector["win"] + vector["push"] + vector["loss"] == pytest.approx(1)
    assert result["net"]["ev"] == pytest.approx(.8)
    assert result["status"] == "RESEARCH_ONLY"
    assert not result["qualified"]


def test_integer_joint_vectors_and_payoff_disagreement_are_not_marginal_medians():
    vectors = {
        "Bovada": (.48, .07, .45),
        "FanDuel": (.46, .05, .49),
        "Circa": (.50, .01, .49),
    }
    quotes = []
    for book, (win, push, _loss) in vectors.items():
        quotes += pair(book, win, market="total", line=44.5)
        quotes += pair(book, win + push, market="total", line=43.5)
    quote_input = input_quote(
        line=44, push_return="8", settlement_profile=profile_ref(INTEGER_TOTAL_PROFILE)
    )
    result = evaluate(quote_input, GAME, quotes, SETTINGS, [], NOW,
                      registry(INTEGER_TOTAL_PROFILE))
    probability = result["probability"]
    assert (probability["win"], probability["push"], probability["loss"]) == pytest.approx((.48, .03, .49))
    assert sum((probability["win"], probability["push"], probability["loss"])) == pytest.approx(1)
    assert probability["disagreement"]["tie_or_push_pp"] == pytest.approx(6)
    assert probability["disagreement"]["loss_pp"] == pytest.approx(4)
    assert probability["disagreement"]["payoff_return"] == pytest.approx(.56)
    assert not result["qualified"]


def test_multi_outcome_break_even_and_stress_move_win_mass_to_loss():
    quote_input = input_quote(
        line=44, total_cost="8", winning_payout="20", push_return="8", losing_return="2"
    )
    quotes = references(line=44.5, probability=.4) + references(line=43.5, probability=.5)
    result = evaluate(quote_input, GAME, quotes, SETTINGS, [], NOW)
    assert result["net"]["scenarios"][0]["expected_return"] == pytest.approx(9.8)
    assert result["net"]["scenarios"][0]["stress_return"] == pytest.approx(9.44)
    assert result["net"]["break_even_probability"] == pytest.approx(.3)


def test_break_even_reports_nonunique_none_and_reversed_profitability():
    nonunique = evaluate(
        input_quote(total_cost="10", winning_payout="10", losing_return="10"),
        GAME, references(probability=.5), SETTINGS, [], NOW,
    )["net"]["break_even"][0]
    assert nonunique == {
        "tie_or_push_probability": 0.0,
        "win_probability": None,
        "win_probability_exact": None,
        "feasible": True,
        "reason": "NON_UNIQUE_BREAK_EVEN",
        "positive_ev_when": "NO_POSITIVE_EV_PROBABILITY",
    }

    all_positive = evaluate(
        input_quote(total_cost="9", winning_payout="10", losing_return="10"),
        GAME, references(probability=.5), SETTINGS, [], NOW,
    )["net"]["break_even"][0]
    none_positive = evaluate(
        input_quote(total_cost="11", winning_payout="10", losing_return="10"),
        GAME, references(probability=.5), SETTINGS, [], NOW,
    )["net"]["break_even"][0]
    assert all_positive["reason"] == "NO_BREAK_EVEN_ALL_POSITIVE"
    assert all_positive["positive_ev_when"] == "ALL_FEASIBLE_WIN_PROBABILITIES"
    assert none_positive["reason"] == "NO_BREAK_EVEN_NONE_POSITIVE"
    assert none_positive["positive_ev_when"] == "NO_POSITIVE_EV_PROBABILITY"

    reversed_returns = evaluate(
        input_quote(total_cost="8", winning_payout="2", losing_return="10"),
        GAME, references(probability=.5), SETTINGS, [], NOW,
    )["net"]["break_even"][0]
    assert reversed_returns["win_probability"] == pytest.approx(.25)
    assert reversed_returns["positive_ev_when"] == "WIN_PROBABILITY_BELOW_BREAK_EVEN"


def test_stake_cap_uses_exact_decimal_percentages_before_cent_flooring():
    settings = {
        "bankroll": "0.03",
        "stake_pct": "33.34",
        "game_cap_pct": "100",
        "open_cap_pct": "100",
    }
    assert stake_cap(settings, [], GAME["id"], "paper")["cap"] == .01


def test_nonfinite_money_lines_and_returns_are_rejected():
    with pytest.raises(ValueError):
        input_quote(outcome_returns={"win": "NaN", "tie_or_push": None, "loss": "0"})
    with pytest.raises(ValueError):
        Pick(game_id=GAME["id"], market="spread", side="home", line=float("inf"))
    with pytest.raises(ValueError):
        american_to_decimal(float("inf"))
