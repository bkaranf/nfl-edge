from datetime import UTC, datetime

import pytest

from backend.domain import QuoteInput
from backend.service import _closing_financial_preflight


NOW = datetime(2026, 9, 15, 12, tzinfo=UTC)
MISSING = object()


def stored_quote(**updates):
    values = {
        "game_id": "20260917_BUF_DET",
        "market": "total",
        "side": "over",
        "line": 44.5,
        "total_cost": "8",
        "winning_payout": "20",
        "push_return": None,
        "losing_return": "0",
        "observed_at": NOW,
        "exchange": "Kalshi",
        "fees_confirmed": True,
    }
    values.update(updates)
    return QuoteInput(**values)


def pinned_evaluation(*, requirement=None, compatible=MISSING, resolved=True, reason_codes=()):
    snapshot = None
    if resolved:
        snapshot = {
            "profile_id": "test.synthetic.adapter-table",
            "version": 1,
            "outcome_rules": {
                "win": {"requirement": "REQUIRED", "exact": None},
                "tie_or_push": {"requirement": requirement, "exact": None},
                "loss": {"requirement": "REQUIRED", "exact": "0"},
            },
            "evidence_ids": ["synthetic:test-only"],
        }
    settlement = {"resolved": snapshot}
    if compatible is not MISSING:
        settlement["compatible"] = compatible
    return {
        "reason_codes": list(reason_codes),
        "calculation": {"settlement_profile": settlement},
    }


@pytest.mark.parametrize(
    "case,evaluation,quote,admissible,tie_possible,reason_code",
    [
        (
            "valid_post_no_tie",
            pinned_evaluation(requirement="FORBIDDEN", compatible=True),
            stored_quote(market="moneyline", side="home", line=None),
            True,
            False,
            None,
        ),
        (
            "valid_regular_explicit_zero_tie",
            pinned_evaluation(requirement="REQUIRED", compatible=True),
            stored_quote(
                market="moneyline", side="home", line=None, push_return="0"
            ),
            True,
            True,
            None,
        ),
        (
            "known_required_tie_missing_without_legacy_issue_code",
            pinned_evaluation(requirement="REQUIRED", compatible=False),
            stored_quote(market="moneyline", side="home", line=None),
            False,
            None,
            "OUTCOME_RETURN_REQUIRED",
        ),
        (
            "unknown_moneyline_tie_missing",
            pinned_evaluation(resolved=False),
            stored_quote(market="moneyline", side="home", line=None),
            False,
            None,
            "OUTCOME_RETURN_REQUIRED",
        ),
        (
            "unknown_integer_push_missing",
            pinned_evaluation(resolved=False),
            stored_quote(line=44),
            False,
            None,
            "OUTCOME_RETURN_REQUIRED",
        ),
        (
            "unknown_loss_missing",
            pinned_evaluation(resolved=False),
            stored_quote(losing_return=None),
            False,
            None,
            "OUTCOME_RETURN_REQUIRED",
        ),
        (
            "known_profile_contradiction",
            pinned_evaluation(
                requirement="FORBIDDEN",
                compatible=False,
                reason_codes=("SETTLEMENT_PROFILE_CONTRADICTION",),
            ),
            stored_quote(losing_return="1"),
            False,
            None,
            "SETTLEMENT_PROFILE_CONTRADICTION",
        ),
        (
            "resolved_profile_missing_compatibility_proof",
            pinned_evaluation(requirement="FORBIDDEN"),
            stored_quote(),
            False,
            None,
            "SETTLEMENT_PROFILE_CONTRADICTION",
        ),
        (
            "unknown_profile_complete_diagnostic",
            pinned_evaluation(resolved=False, compatible=False),
            stored_quote(),
            True,
            None,
            None,
        ),
        (
            "complete_economics_can_continue_to_reference_check",
            pinned_evaluation(resolved=False),
            stored_quote(),
            True,
            None,
            None,
        ),
    ],
)
def test_closing_financial_preflight_decision_table(
    case, evaluation, quote, admissible, tie_possible, reason_code
):
    result = _closing_financial_preflight(evaluation, quote)
    assert result["admissible"] is admissible, case
    assert result["tie_possible"] is tie_possible, case
    assert result.get("reason_code") == reason_code, case
