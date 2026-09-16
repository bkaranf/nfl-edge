"""Immutable record requests and canonical hashing for durable history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
import hashlib
import json
from typing import Any, Literal, Mapping, Sequence

from pydantic import Field, field_validator, model_validator

from backend.domain import QuoteInput, RequestModel, Settlement, dt, iso


INTENT_HEADER = "X-NFL-Edge-Intent"
INTENT_HEADER_VALUE = "local-write-v1"


class EvaluationLinkState(str, Enum):
    PINNED = "PINNED"
    UNAVAILABLE = "UNAVAILABLE"
    LEGACY_UNKNOWN = "LEGACY_UNKNOWN"


class AcceptedCalculationState(str, Enum):
    ORIGINAL_TERMS = "ORIGINAL_TERMS"
    PINNED_REPRICE = "PINNED_REPRICE"
    UNAVAILABLE = "UNAVAILABLE"
    LEGACY_UNKNOWN = "LEGACY_UNKNOWN"


class HistoryReason(str, Enum):
    MISSING_EVALUATION_ID = "MISSING_EVALUATION_ID"
    EVALUATION_NOT_FOUND = "EVALUATION_NOT_FOUND"
    CONTRIBUTOR_PROVENANCE_INCOMPLETE = "CONTRIBUTOR_PROVENANCE_INCOMPLETE"
    REFERENCE_RECEIVED_AFTER_EVALUATION = "REFERENCE_RECEIVED_AFTER_EVALUATION"
    REFERENCE_RECEIVED_AFTER_ACCEPTANCE = "REFERENCE_RECEIVED_AFTER_ACCEPTANCE"
    ACCEPTANCE_PRECEDES_EVALUATION = "ACCEPTANCE_PRECEDES_EVALUATION"
    EVALUATION_EXPIRED_AT_ACCEPTANCE = "EVALUATION_EXPIRED_AT_ACCEPTANCE"
    EVENT_IDENTITY_MISMATCH = "EVENT_IDENTITY_MISMATCH"
    SELECTION_IDENTITY_MISMATCH = "SELECTION_IDENTITY_MISMATCH"
    ECONOMIC_IDENTITY_MISMATCH = "ECONOMIC_IDENTITY_MISMATCH"
    PROFILE_IDENTITY_MISMATCH = "PROFILE_IDENTITY_MISMATCH"
    SETTINGS_REVISION_CHANGED = "SETTINGS_REVISION_CHANGED"
    SOURCE_REVISION_CHANGED = "SOURCE_REVISION_CHANGED"
    EVENT_REVISION_CHANGED = "EVENT_REVISION_CHANGED"
    LEGACY_PROVENANCE_UNKNOWN = "LEGACY_PROVENANCE_UNKNOWN"


class SaveEntryIntent(QuoteInput):
    """Flat compatible entry request with explicit history fields."""

    idempotency_key: str = Field(min_length=8, max_length=160, pattern=r"^[A-Za-z0-9._:-]+$")
    evaluation_id: str | None = Field(default=None, min_length=8, max_length=80)
    accepted_at: datetime | None = None
    placed_confirmed: bool = False
    receipt_identity: str | None = Field(default=None, max_length=300)
    notes: str = Field(default="", max_length=1000)

    @field_validator("accepted_at")
    @classmethod
    def accepted_timezone_required(cls, value):
        return None if value is None else dt(value)

    @model_validator(mode="after")
    def actual_confirmation_required(self):
        if self.mode == "actual" and (self.accepted_at is None or not self.placed_confirmed):
            raise ValueError(
                "Actual entries require accepted_at and confirmation that the position was placed."
            )
        return self


class SettlementIntent(Settlement):
    idempotency_key: str = Field(min_length=8, max_length=160, pattern=r"^[A-Za-z0-9._:-]+$")
    occurred_at: datetime | None = None
    receipt_identity: str | None = Field(default=None, max_length=300)

    @field_validator("occurred_at")
    @classmethod
    def occurred_timezone_required(cls, value):
        return None if value is None else dt(value)


class ReopenIntent(RequestModel):
    idempotency_key: str = Field(min_length=8, max_length=160, pattern=r"^[A-Za-z0-9._:-]+$")
    occurred_at: datetime | None = None
    notes: str = Field(default="", max_length=1000)

    @field_validator("occurred_at")
    @classmethod
    def occurred_timezone_required(cls, value):
        return None if value is None else dt(value)


class ClosingRevisionIntent(RequestModel):
    idempotency_key: str = Field(min_length=8, max_length=200, pattern=r"^[A-Za-z0-9._:-]+$")
    payload: dict[str, Any]


class ManualEventIntent(RequestModel):
    idempotency_key: str = Field(min_length=8, max_length=160, pattern=r"^[A-Za-z0-9._:-]+$")
    home: str = Field(min_length=2, max_length=80)
    away: str = Field(min_length=2, max_length=80)
    kickoff: datetime
    season: int = Field(ge=2000, le=2200)
    phase: Literal["PRE", "REG", "POST"]
    week: int | None = Field(default=None, ge=0, le=30)
    venue: str | None = Field(default=None, max_length=200)
    observed_at: datetime
    notes: str = Field(default="", max_length=1000)

    @field_validator("kickoff", "observed_at")
    @classmethod
    def timezones_required(cls, value):
        return dt(value)


class ScheduleRevisionIntent(RequestModel):
    idempotency_key: str = Field(min_length=8, max_length=160, pattern=r"^[A-Za-z0-9._:-]+$")
    kickoff: datetime
    status: Literal["scheduled", "live", "final", "postponed", "cancelled"] = "scheduled"
    season: int = Field(ge=2000, le=2200)
    phase: Literal["PRE", "REG", "POST"]
    week: int | None = Field(default=None, ge=0, le=30)
    venue: str | None = Field(default=None, max_length=200)
    observed_at: datetime
    notes: str = Field(default="", max_length=1000)

    @field_validator("kickoff", "observed_at")
    @classmethod
    def timezones_required(cls, value):
        return dt(value)


class ProviderEventMappingIntent(RequestModel):
    idempotency_key: str = Field(min_length=8, max_length=160, pattern=r"^[A-Za-z0-9._:-]+$")
    source_id: str = Field(min_length=1, max_length=80)
    provider_event_id: str = Field(min_length=1, max_length=240)
    event_id: str = Field(min_length=8, max_length=80)
    evidence: dict[str, Any]
    reviewed: bool = False


class EventMappingQuarantineIntent(RequestModel):
    idempotency_key: str = Field(min_length=8, max_length=160, pattern=r"^[A-Za-z0-9._:-]+$")
    source_id: str = Field(min_length=1, max_length=80)
    provider_event_id: str = Field(min_length=1, max_length=240)
    candidate: dict[str, Any]
    reason_codes: tuple[str, ...] = Field(min_length=1)


class SourcePolicyRevisionDraft(RequestModel):
    source_id: str = Field(min_length=1, max_length=80)
    effective_at: datetime
    admission_state: Literal[
        "UNASSESSED", "RESEARCH_ONLY", "ELIGIBLE", "DEGRADED", "DISABLED"
    ] = "UNASSESSED"
    collection_mode: Literal["DISABLED", "MANUAL_ONLY", "ON_DEMAND"] = "DISABLED"
    scope: dict[str, Any] = Field(default_factory=dict)
    access: dict[str, Any] = Field(default_factory=dict)
    freshness: dict[str, Any] = Field(default_factory=dict)
    cache: dict[str, Any] = Field(default_factory=dict)
    rate_policy: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    reason: str = Field(default="", max_length=1000)

    @field_validator("effective_at")
    @classmethod
    def effective_timezone_required(cls, value):
        return dt(value)


class SourceSnapshotDraft(RequestModel):
    source_id: str = Field(min_length=1, max_length=80)
    policy_revision_id: str | None = Field(default=None, max_length=80)
    scope: dict[str, Any] = Field(default_factory=dict)
    request_started_at: datetime | None = None
    response_received_at: datetime
    monotonic_duration_ms: int | None = Field(default=None, ge=0)
    parser_revision: str | None = Field(default=None, max_length=120)
    completeness: Literal["FULL", "PARTIAL", "UNKNOWN"] = "UNKNOWN"
    status: Literal["SUCCESS", "EMPTY", "ERROR", "SUSPENDED"]
    error: str | None = Field(default=None, max_length=1000)
    raw_evidence: Any = None
    clock_issues: tuple[str, ...] = ()

    @field_validator("request_started_at", "response_received_at")
    @classmethod
    def timezones_required(cls, value):
        return None if value is None else dt(value)


class QuoteObservationDraft(RequestModel):
    pair_id: str = Field(min_length=1, max_length=160)
    event_id: str | None = Field(default=None, max_length=80)
    provider_event_id: str | None = Field(default=None, max_length=240)
    provider_market_id: str | None = Field(default=None, max_length=240)
    provider_outcome_id: str | None = Field(default=None, max_length=240)
    origin_book: str = Field(min_length=1, max_length=120)
    distributor: str | None = Field(default=None, max_length=120)
    market: Literal["moneyline", "spread", "total"]
    period: str = Field(default="full_game", max_length=80)
    rule_identity: str | None = Field(default=None, max_length=240)
    side: Literal["home", "away", "over", "under"]
    raw_line: str | None = Field(default=None, max_length=80)
    canonical_line: float | None = None
    decimal_price: float
    state: Literal["OPEN", "OFF", "SUSPENDED", "CLOSED"] = "OPEN"
    provider_timestamp: datetime | None = None
    provider_timestamp_meaning: str | None = Field(default=None, max_length=240)
    source_observed_at: datetime
    raw_locator: str | None = Field(default=None, max_length=500)
    raw_hash: str | None = Field(default=None, max_length=128)
    extras: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider_timestamp", "source_observed_at")
    @classmethod
    def timezones_required(cls, value):
        return None if value is None else dt(value)


@dataclass(frozen=True)
class EvaluationBundleDraft:
    target: Mapping[str, Any]
    original_monetary_strings: Mapping[str, Any]
    result: Mapping[str, Any]
    reference_inputs: Sequence[Mapping[str, Any]]
    settings: Mapping[str, Any]
    game: Mapping[str, Any]
    revision_ids: Mapping[str, Any]
    expires_at: str | None


@dataclass(frozen=True)
class EntryRecordDraft:
    payload: Mapping[str, Any]
    event_id: str | None
    evaluation_id: str | None
    mode: str
    accepted_at: str | None
    target_observed_at: str
    link_state: str


@dataclass(frozen=True)
class IntentResult:
    resource: dict[str, Any]
    replayed: bool
    resource_id: str


def _decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def canonical_value(value: Any) -> Any:
    """Normalize validated data for equivalence; preserve exact text elsewhere."""
    if isinstance(value, Decimal):
        return _decimal_text(value)
    if isinstance(value, datetime):
        return iso(value)
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "model_dump"):
        return canonical_value(value.model_dump(mode="python"))
    if isinstance(value, Mapping):
        return {str(key): canonical_value(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [canonical_value(item) for item in value]
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        canonical_value(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def intent_hash(kind: str, target_id: str, value: Any) -> str:
    return content_hash({"kind": kind, "target_id": target_id, "request": value})
