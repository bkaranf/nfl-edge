"""Immutable settlement-profile registry and compatibility checks.

Production intentionally starts with no admitted profiles. Tests may inject
synthetic profiles directly into the pricing engine; they are never added to
the production registry or exposed as user-selectable contract evidence.
"""
from __future__ import annotations

from hashlib import sha256
import json
from datetime import datetime
from types import MappingProxyType
from typing import Mapping

from backend.domain import (
    Outcome,
    ProfileAdmission,
    QuoteInput,
    ReasonCode,
    ReturnRequirement,
    SettlementProfile,
)

ProfileKey = tuple[str, int]
ProfileRegistry = Mapping[ProfileKey, SettlementProfile]

def profile_key(profile: SettlementProfile) -> ProfileKey:
    return profile.profile_id, profile.version


def calculate_profile_hash(profile: SettlementProfile) -> str:
    payload = profile.model_dump(mode="json", exclude={"content_hash"})
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def build_profile(**fields) -> SettlementProfile:
    """Build a content-addressed profile, primarily for bounded test fixtures."""
    profile = SettlementProfile(content_hash="pending", **fields)
    return profile.model_copy(update={"content_hash": calculate_profile_hash(profile)})


def build_registry(profiles) -> ProfileRegistry:
    registry: dict[ProfileKey, SettlementProfile] = {}
    for profile in profiles:
        key = profile_key(profile)
        previous = registry.get(key)
        if previous is not None and previous.content_hash != profile.content_hash:
            raise ValueError(
                f"Duplicate settlement profile {key[0]} v{key[1]} has conflicting content"
            )
        if profile.content_hash != calculate_profile_hash(profile):
            raise ValueError(f"Settlement profile {key[0]} v{key[1]} has an invalid content hash")
        registry[key] = profile
    return MappingProxyType(registry)


# No supplied evidence is sufficient to admit a real production profile.
PROFILE_REGISTRY: ProfileRegistry = build_registry(())


def profile_snapshot(profile: SettlementProfile) -> dict:
    # Store the complete immutable semantics so an evaluation remains reproducible
    # even if the active registry later changes.
    return profile.model_dump(mode="json")


def list_profiles(registry: ProfileRegistry | None = None, *, admitted_only: bool = False) -> list[dict]:
    selected = registry if registry is not None else PROFILE_REGISTRY
    profiles = sorted(selected.values(), key=lambda item: (item.profile_id, item.version))
    if admitted_only:
        profiles = [item for item in profiles if item.admission == ProfileAdmission.ADMITTED]
    return [profile_snapshot(item) for item in profiles]


def _issue(code: ReasonCode, message: str, field: str | None = None, **context) -> dict:
    issue = {"code": code.value, "message": message}
    if field:
        issue["field"] = field
    if context:
        issue["context"] = context
    return issue


def resolve_profile(
    quote: QuoteInput,
    game: dict,
    registry: ProfileRegistry | None = None,
    *,
    as_of: datetime,
) -> dict:
    selected = registry if registry is not None else PROFILE_REGISTRY
    requested = quote.settlement_profile.model_dump(mode="json") if quote.settlement_profile else None
    if quote.settlement_profile is None:
        return {
            "requested": None,
            "profile": None,
            "snapshot": None,
            "compatible": False,
            "admitted": False,
            "issues": [_issue(
                ReasonCode.SETTLEMENT_PROFILE_REQUIRED,
                "Choose a versioned settlement profile supported by server-side evidence.",
                "settlement_profile",
            )],
        }

    key = (quote.settlement_profile.profile_id, quote.settlement_profile.version)
    profile = selected.get(key)
    if profile is None:
        return {
            "requested": requested,
            "profile": None,
            "snapshot": None,
            "compatible": False,
            "admitted": False,
            "issues": [_issue(
                ReasonCode.SETTLEMENT_PROFILE_UNKNOWN,
                "The requested settlement profile is not present in the server registry.",
                "settlement_profile",
                profile_id=key[0],
                version=key[1],
            )],
        }

    issues: list[dict] = []
    contradictions = []
    if profile.content_hash != calculate_profile_hash(profile):
        contradictions.append("content hash")
    if quote.exchange != profile.exchange:
        contradictions.append("exchange")
    if quote.market != profile.market:
        contradictions.append("market")
    if quote.period != profile.period:
        contradictions.append("period")
    if game.get("season_type") not in profile.season_types:
        contradictions.append("season type")
    if not profile.overtime_included:
        contradictions.append("overtime treatment")
    tie_rule = profile.outcome_rules[Outcome.TIE_OR_PUSH]
    integer = quote.market != "moneyline" and quote.line is not None and quote.line == int(quote.line)
    if quote.market == "moneyline" and game.get("season_type") == "REG" and tie_rule.requirement == ReturnRequirement.FORBIDDEN:
        contradictions.append("regular-season tie outcome")
    if quote.market != "moneyline" and not integer and tie_rule.requirement == ReturnRequirement.REQUIRED:
        contradictions.append("half-point tie/push outcome")
    if integer and tie_rule.requirement == ReturnRequirement.FORBIDDEN:
        contradictions.append("integer push outcome")
    if contradictions:
        issues.append(_issue(
            ReasonCode.SETTLEMENT_PROFILE_CONTRADICTION,
            "The entered quote contradicts the requested settlement profile.",
            "settlement_profile",
            conflicts=contradictions,
        ))

    observed_at = quote.observed_at
    if (observed_at < profile.effective_from or as_of < profile.effective_from
            or (profile.effective_to is not None
                and (observed_at >= profile.effective_to or as_of >= profile.effective_to))):
        issues.append(_issue(
            ReasonCode.SETTLEMENT_PROFILE_NOT_EFFECTIVE,
            "The settlement profile was not effective throughout observation and evaluation.",
            "settlement_profile",
        ))

    values = {
        Outcome.WIN: quote.outcome_returns.win,
        Outcome.TIE_OR_PUSH: quote.outcome_returns.tie_or_push,
        Outcome.LOSS: quote.outcome_returns.loss,
    }
    for outcome in (Outcome.WIN, Outcome.TIE_OR_PUSH, Outcome.LOSS):
        rule = profile.outcome_rules[outcome]
        value = values[outcome]
        if rule.requirement == ReturnRequirement.REQUIRED and value is None:
            issues.append(_issue(
                ReasonCode.OUTCOME_RETURN_REQUIRED,
                f"Enter the total net return for the {outcome.value} outcome.",
                f"outcome_returns.{outcome.value}",
                outcome=outcome.value,
            ))
        elif rule.requirement == ReturnRequirement.FORBIDDEN and value is not None:
            issues.append(_issue(
                ReasonCode.SETTLEMENT_PROFILE_CONTRADICTION,
                f"The profile does not admit a {outcome.value} outcome return.",
                f"outcome_returns.{outcome.value}",
                outcome=outcome.value,
            ))
        elif rule.exact is not None and value is not None and value != rule.exact:
            issues.append(_issue(
                ReasonCode.SETTLEMENT_PROFILE_CONTRADICTION,
                f"The entered {outcome.value} return contradicts the profile.",
                f"outcome_returns.{outcome.value}",
                outcome=outcome.value,
                expected=str(rule.exact),
                entered=str(value),
            ))

    if (profile.admission != ProfileAdmission.ADMITTED
            or profile.admitted_at is None or profile.admitted_at > as_of):
        issues.append(_issue(
            ReasonCode.SETTLEMENT_PROFILE_NOT_ADMITTED,
            "The settlement profile is not admitted for screen qualification.",
            "settlement_profile",
            admission=profile.admission.value,
            admitted_at=profile.admitted_at.isoformat() if profile.admitted_at else None,
            as_of=as_of.isoformat(),
        ))

    incompatible_codes = {
        ReasonCode.SETTLEMENT_PROFILE_CONTRADICTION.value,
        ReasonCode.OUTCOME_RETURN_REQUIRED.value,
    }
    compatible = not any(item["code"] in incompatible_codes for item in issues)
    effective = not any(item["code"] == ReasonCode.SETTLEMENT_PROFILE_NOT_EFFECTIVE.value for item in issues)
    admission_current = not any(item["code"] == ReasonCode.SETTLEMENT_PROFILE_NOT_ADMITTED.value for item in issues)
    admitted = compatible and effective and admission_current
    return {
        "requested": requested,
        "profile": profile,
        "snapshot": profile_snapshot(profile),
        "compatible": compatible,
        "admitted": admitted,
        "issues": issues,
    }
