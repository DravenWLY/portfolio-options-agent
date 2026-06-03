"""Provider-neutral Market Mood read contracts."""

from datetime import datetime
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


MarketMoodDataMode: TypeAlias = Literal["synthetic", "provider_reference", "unavailable"]
MarketMoodFreshnessStatus: TypeAlias = Literal["fresh", "stale", "unavailable"]
MarketMoodRating: TypeAlias = Literal["extreme_fear", "fear", "neutral", "greed", "extreme_greed", "unknown"]
MarketMoodComparisonWindow: TypeAlias = Literal["1w", "1m", "1y"]
MarketMoodRefreshStatus: TypeAlias = Literal["refreshed", "failed"]

PROHIBITED_MARKET_MOOD_PHRASES = (
    "i recommend",
    "recommendation",
    "buy ",
    "sell ",
    "risk-on",
    "risk-off",
    "safe-to-trade",
    "safe to trade",
    "ready-to-trade",
    "ready to trade",
    "guaranteed return",
    "urgent",
    "urgency",
    "place order",
    "submit order",
    "execute trade",
)


def validate_market_mood_payload(value: object) -> None:
    """Reject private fields and advice/execution wording in Market Mood responses."""

    forbidden = find_forbidden_keys(value, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    if forbidden:
        raise ValueError(f"market mood payload contains forbidden private fields: {sorted(forbidden)}")
    rendered = repr(value).lower()
    for phrase in PROHIBITED_MARKET_MOOD_PHRASES:
        if phrase in rendered:
            raise ValueError(f"market mood payload contains prohibited wording: {phrase}")


class MarketMoodTrendPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    date: str
    score: float | None = None
    score_label: str | None = None
    rating: MarketMoodRating
    rating_label: str


class MarketMoodComparisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    window: MarketMoodComparisonWindow
    prior_score: float | None = None
    prior_score_label: str | None = None
    change_label: str | None = None
    is_available: bool


class MarketMoodComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    component_key: str
    display_name: str
    score: float | None = None
    score_label: str | None = None
    rating: MarketMoodRating
    rating_label: str


class MarketMoodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: MarketMoodDataMode
    source_label: str
    source_detail_label: str
    source_rights_notice: str
    generated_at: datetime
    updated_at_utc: datetime | None = None
    updated_at_label: str | None = None
    freshness_status: MarketMoodFreshnessStatus
    freshness_label: str
    is_trading_signal: bool
    is_actionability_input: bool
    is_risk_rule_input: bool
    score: float | None = None
    score_label: str | None = None
    score_min: int = Field(default=0)
    score_max: int = Field(default=100)
    rating: MarketMoodRating
    rating_label: str
    trend_series: tuple[MarketMoodTrendPointRead, ...]
    comparisons: tuple[MarketMoodComparisonRead, ...]
    components: tuple[MarketMoodComponentRead, ...]
    caveat_codes: tuple[str, ...]
    limitations: tuple[str, ...]
    status_message: str | None = None

    @model_validator(mode="after")
    def market_mood_read_must_be_safe(self) -> "MarketMoodRead":
        if self.is_trading_signal or self.is_actionability_input or self.is_risk_rule_input:
            raise ValueError("market mood must not be a signal, actionability input, or risk-rule input")
        if self.score_min != 0 or self.score_max != 100:
            raise ValueError("market mood score range must remain 0-100")
        validate_market_mood_payload(self.model_dump(mode="python"))
        return self


class MarketMoodRefreshStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    status: MarketMoodRefreshStatus
    data_mode: MarketMoodDataMode
    source_label: str
    generated_at: datetime | None = None
    updated_at_utc: datetime | None = None
    record_count: int
    message: str

    @model_validator(mode="after")
    def refresh_status_must_be_safe(self) -> "MarketMoodRefreshStatusRead":
        validate_market_mood_payload(self.model_dump(mode="python"))
        return self
