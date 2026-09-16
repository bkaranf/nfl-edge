"""Canonical NFL identities, times and request validation."""
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN
from enum import Enum
import re
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, PrivateAttr, field_validator, model_validator

TEAMS = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}
EASTERN = ZoneInfo("America/New_York")
BOOKS = ["DraftKings", "Bovada", "FanDuel", "BetMGM", "Caesars", "Pinnacle", "Circa", "BetRivers", "BetOnline"]


def utcnow() -> datetime:
    return datetime.now(UTC)


def iso(value: datetime | None = None) -> str:
    return (value or utcnow()).astimezone(UTC).isoformat(timespec="milliseconds")


def dt(value: str | datetime) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("A timezone is required")
    return parsed.astimezone(UTC)


def age(value: str, now: datetime | None = None) -> float:
    return ((now or utcnow()) - dt(value)).total_seconds()


def team_code(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]", "", value.lower())
    aliases = {"jac": "JAX", "jax": "JAX", "la": "LAR", "lar": "LAR", "wsh": "WAS",
               "newyorkg": "NYG", "newyorkj": "NYJ", "losangelesc": "LAC", "losangelesr": "LAR",
               "washington": "WAS", "oak": "LV", "sd": "LAC", "stl": "LAR"}
    if cleaned in aliases:
        return aliases[cleaned]
    for code, name in TEAMS.items():
        city = name.rsplit(" ", 1)[0]
        variants = (code, name, name.split(" ")[-1], city)
        if cleaned in {re.sub(r"[^a-z0-9]", "", s.lower()) for s in variants}:
            if cleaned in ("newyork", "losangeles"):
                raise ValueError(f"Ambiguous team: {value}")
            return code
    raise ValueError(f"Unrecognized NFL team: {value}")


def game(home: str, away: str, start: str | datetime, **extras) -> dict:
    h, a, when = team_code(home), team_code(away), dt(start)
    return {"id": f"{when.astimezone(EASTERN):%Y-%m-%d}-{a}-{h}", "home": h, "away": a,
            "home_name": TEAMS[h], "away_name": TEAMS[a], "start_time": iso(when),
            "status": "scheduled", "season_type": "REG", **extras}


def american_to_decimal(value: float) -> float:
    if not (-100000 <= value <= -100 or 100 <= value <= 100000):
        raise ValueError("Use American odds of +100 or greater, or -100 or less")
    return 1 + (value / 100 if value > 0 else 100 / abs(value))


def decimal_to_american(value: float) -> int:
    if value <= 1:
        raise ValueError("Decimal odds must be above 1")
    return round(100 * (value - 1)) if value >= 2 else round(-100 / (value - 1))


def cents(value: Decimal | float | str) -> int:
    return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_DOWN))


def canonical_line(market: str, side: str, line: float | None) -> float | None:
    if line is None:
        return None
    return round(-line if market == "spread" and side == "away" else line, 3)


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EvaluationStatus(str, Enum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    MEETS_ESTIMATED_SCREEN = "MEETS_ESTIMATED_SCREEN"
    EXPIRED = "EXPIRED"


class ReasonCode(str, Enum):
    EVENT_NOT_PREGAME = "EVENT_NOT_PREGAME"
    REFERENCE_PAIR_MISSING = "REFERENCE_PAIR_MISSING"
    INTEGER_ADJACENT_PAIRS_MISSING = "INTEGER_ADJACENT_PAIRS_MISSING"
    INSUFFICIENT_ELIGIBLE_REFERENCES = "INSUFFICIENT_ELIGIBLE_REFERENCES"
    REFERENCE_DISAGREEMENT = "REFERENCE_DISAGREEMENT"
    QUOTE_STALE = "QUOTE_STALE"
    QUOTE_TIMESTAMP_IN_FUTURE = "QUOTE_TIMESTAMP_IN_FUTURE"
    FEES_UNCONFIRMED = "FEES_UNCONFIRMED"
    SETTLEMENT_PROFILE_REQUIRED = "SETTLEMENT_PROFILE_REQUIRED"
    SETTLEMENT_PROFILE_UNKNOWN = "SETTLEMENT_PROFILE_UNKNOWN"
    SETTLEMENT_PROFILE_NOT_ADMITTED = "SETTLEMENT_PROFILE_NOT_ADMITTED"
    SETTLEMENT_PROFILE_NOT_EFFECTIVE = "SETTLEMENT_PROFILE_NOT_EFFECTIVE"
    SETTLEMENT_PROFILE_CONTRADICTION = "SETTLEMENT_PROFILE_CONTRADICTION"
    OUTCOME_RETURN_REQUIRED = "OUTCOME_RETURN_REQUIRED"
    INTEGER_LINE_RESEARCH_ONLY = "INTEGER_LINE_RESEARCH_ONLY"
    ROI_BELOW_MINIMUM = "ROI_BELOW_MINIMUM"
    STRESSED_ROI_NOT_POSITIVE = "STRESSED_ROI_NOT_POSITIVE"


class ProfileAdmission(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    ADMITTED = "ADMITTED"
    RETIRED = "RETIRED"


class Outcome(str, Enum):
    WIN = "win"
    TIE_OR_PUSH = "tie_or_push"
    LOSS = "loss"


class ReturnRequirement(str, Enum):
    REQUIRED = "REQUIRED"
    FORBIDDEN = "FORBIDDEN"


class SettlementProfileRef(RequestModel):
    profile_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,79}$")
    version: int = Field(ge=1, le=1000000)


class NetOutcomeReturns(RequestModel):
    win: Decimal = Field(ge=0, le=10000000, decimal_places=2)
    tie_or_push: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)
    loss: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)


class OutcomeReturnRule(RequestModel):
    requirement: ReturnRequirement
    exact: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)

    @model_validator(mode="after")
    def exact_only_for_required(self):
        if self.requirement == ReturnRequirement.FORBIDDEN and self.exact is not None:
            raise ValueError("A forbidden outcome cannot specify an exact return")
        return self


class SettlementProfile(RequestModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    profile_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,79}$")
    version: int = Field(ge=1, le=1000000)
    content_hash: str = Field(min_length=1, max_length=96)
    exchange: Literal["UDX", "Kalshi", "Nadex"]
    product: str = Field(min_length=1, max_length=80)
    sport: Literal["NFL"] = "NFL"
    market: Literal["moneyline", "spread", "total"]
    period: Literal["full_game"] = "full_game"
    season_types: tuple[Literal["REG", "POST"], ...]
    overtime_included: bool
    outcome_rules: dict[Outcome, OutcomeReturnRule]
    conditional_on_ordinary_completion: bool = True
    evidence_ids: tuple[str, ...] = ()
    effective_from: datetime
    effective_to: datetime | None = None
    admission: ProfileAdmission = ProfileAdmission.UNVERIFIED
    admitted_at: datetime | None = None
    decision_id: str | None = Field(default=None, max_length=120)

    @field_validator("effective_from", "effective_to", "admitted_at")
    @classmethod
    def profile_timezones_required(cls, value):
        return None if value is None else dt(value)

    @model_validator(mode="after")
    def validate_profile(self):
        expected = {Outcome.WIN, Outcome.TIE_OR_PUSH, Outcome.LOSS}
        if set(self.outcome_rules) != expected:
            raise ValueError("A profile must define win, tie_or_push, and loss return rules")
        if not self.season_types:
            raise ValueError("A profile must identify at least one season type")
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("Profile effective_to must be after effective_from")
        if self.admission == ProfileAdmission.ADMITTED:
            if not self.evidence_ids or self.admitted_at is None or not self.decision_id:
                raise ValueError("An admitted profile requires evidence, admission time, and decision ID")
        return self


class Pick(RequestModel):
    game_id: str = Field(min_length=5, max_length=80)
    market: Literal["moneyline", "spread", "total"]
    side: Literal["home", "away", "over", "under"]
    line: FiniteFloat | None = None
    period: Literal["full_game"] = "full_game"

    @model_validator(mode="after")
    def validate_pick(self):
        if (self.market == "total") != (self.side in ("over", "under")):
            raise ValueError("Selection does not match the market")
        if self.market == "moneyline" and self.line is not None:
            raise ValueError("Moneylines do not have point lines")
        if self.market != "moneyline" and (self.line is None or abs(self.line) > 150 or self.line * 2 != int(self.line * 2)):
            raise ValueError("Use an exact integer or half-point line")
        if self.market == "total" and self.line <= 0:
            raise ValueError("A total must be positive")
        return self


class QuoteInput(Pick):
    total_cost: Decimal = Field(gt=0, le=1000000, decimal_places=2)
    winning_payout: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)
    observed_at: datetime
    exchange: Literal["Unknown", "UDX", "Kalshi", "Nadex"] = "Unknown"
    fees_confirmed: bool = False
    rules_confirmed: bool = False
    push_return: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)
    losing_return: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)
    outcome_returns: NetOutcomeReturns | None = None
    settlement_profile: SettlementProfileRef | None = None
    quantity: Decimal | None = Field(default=None, gt=0, le=1000000000, decimal_places=6)
    contract_id: str | None = Field(default=None, max_length=200)
    mode: Literal["paper", "actual"] = "paper"
    _original_monetary_strings: dict[str, object] = PrivateAttr(default_factory=dict)

    @model_validator(mode="wrap")
    @classmethod
    def capture_original_monetary_strings(cls, value, handler):
        raw = value if isinstance(value, dict) else {}
        nested = raw.get("outcome_returns")
        if isinstance(nested, BaseModel):
            nested = nested.model_dump(mode="json")
        nested = nested if isinstance(nested, dict) else {}

        def text(raw):
            return None if raw is None else str(raw)

        captured = {
            "total_cost": text(raw.get("total_cost")),
            "winning_payout": text(raw.get("winning_payout")),
            "push_return": text(raw.get("push_return")),
            "losing_return": text(raw.get("losing_return")),
            "outcome_returns": {
                "win": text(nested.get("win")),
                "tie_or_push": text(nested.get("tie_or_push")),
                "loss": text(nested.get("loss")),
            },
        }
        model = handler(value)
        model._original_monetary_strings = captured
        return model

    @property
    def original_monetary_strings(self) -> dict[str, object]:
        return self._original_monetary_strings

    @field_validator("observed_at")
    @classmethod
    def timezone_required(cls, value):
        return dt(value)

    @model_validator(mode="after")
    def canonicalize_outcome_returns(self):
        canonical = self.outcome_returns
        if canonical is None:
            if self.winning_payout is None:
                raise ValueError("Provide outcome_returns.win or winning_payout")
            canonical = NetOutcomeReturns(
                win=self.winning_payout,
                tie_or_push=self.push_return,
                loss=self.losing_return,
            )
        else:
            conflicts = []
            if self.winning_payout is not None and self.winning_payout != canonical.win:
                conflicts.append("winning_payout")
            if self.push_return is not None and self.push_return != canonical.tie_or_push:
                conflicts.append("push_return")
            if self.losing_return is not None and self.losing_return != canonical.loss:
                conflicts.append("losing_return")
            if conflicts:
                raise ValueError(
                    "OUTCOME_RETURN_CONTRADICTION: legacy fields disagree with outcome_returns: "
                    + ", ".join(conflicts)
                )
        object.__setattr__(self, "outcome_returns", canonical)
        object.__setattr__(self, "winning_payout", canonical.win)
        object.__setattr__(self, "push_return", canonical.tie_or_push)
        object.__setattr__(self, "losing_return", canonical.loss)
        return self


class SaveBet(QuoteInput):
    placed_confirmed: bool = False
    notes: str = Field(default="", max_length=1000)


class ReferenceInput(RequestModel):
    game_id: str
    market: Literal["moneyline", "spread", "total"]
    book: str
    line: FiniteFloat | None = None
    price_a: FiniteFloat
    price_b: FiniteFloat
    observed_at: datetime
    confirmed: bool = False

    @field_validator("book")
    @classmethod
    def known_book(cls, value):
        for book in BOOKS:
            if value.lower() == book.lower():
                return book
        raise ValueError("Choose a supported reference bookmaker")

    @field_validator("price_a", "price_b")
    @classmethod
    def valid_odds(cls, value):
        american_to_decimal(value)
        return value

    @field_validator("observed_at")
    @classmethod
    def timezone_required(cls, value):
        return dt(value)

    @model_validator(mode="after")
    def valid_line(self):
        Pick(game_id=self.game_id, market=self.market, side="over" if self.market == "total" else "home", line=self.line)
        if not self.confirmed:
            raise ValueError("Confirm that both prices were observed together")
        return self


class Settings(RequestModel):
    bankroll: Decimal = Field(default=Decimal("0"), ge=0, le=10000000, decimal_places=2)
    stake_pct: FiniteFloat = Field(default=0.5, gt=0, le=5)
    game_cap_pct: FiniteFloat = Field(default=1, gt=0, le=10)
    open_cap_pct: FiniteFloat = Field(default=5, gt=0, le=25)
    min_roi_pct: FiniteFloat = Field(default=3, ge=0, le=50)
    stress_pp: FiniteFloat = Field(default=2, ge=0.5, le=10)
    min_books: int = Field(default=3, ge=3, le=9)
    max_age_seconds: int = Field(default=120, ge=30, le=300)
    max_disagreement_pp: FiniteFloat = Field(default=5, ge=1, le=10)
    tie_max_pct: FiniteFloat = Field(default=5, ge=0, le=10)

    @model_validator(mode="after")
    def caps_ordered(self):
        if self.stake_pct > self.game_cap_pct or self.game_cap_pct > self.open_cap_pct:
            raise ValueError("Per-bet size must be <= game cap <= total open cap")
        return self


class Settlement(RequestModel):
    returned: Decimal = Field(ge=0, le=10000000, decimal_places=2)
    result: Literal["win", "loss", "push", "void", "cashout", "other"]
    notes: str = Field(default="", max_length=1000)
