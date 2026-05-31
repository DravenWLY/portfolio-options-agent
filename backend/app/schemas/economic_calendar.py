"""Provider-neutral economic calendar read contracts."""

from datetime import date, datetime
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, model_validator

from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


EconomicCalendarDataMode: TypeAlias = Literal["synthetic", "replay", "provider_reference", "unavailable"]
EconomicEventImportance: TypeAlias = Literal["high", "medium", "low", "unknown"]
EconomicEventImportanceSource: TypeAlias = Literal["provider", "app_classified", "unavailable"]
EconomicEventType: TypeAlias = Literal["economic_release", "central_bank", "holiday", "speech", "other"]
EconomicCalendarRefreshStatus: TypeAlias = Literal["refreshed", "failed"]

PROHIBITED_ECONOMIC_CALENDAR_PHRASES = (
    "buy because",
    "sell because",
    "trade this",
    "trade signal",
    "market will",
    "hot event",
    "must watch",
    "safe to trade",
    "ready to trade",
    "guaranteed",
    "recommendation",
    "top event to trade",
    "ai pick",
    "place order",
    "submit order",
    "execute trade",
)


def validate_economic_calendar_payload(value: object) -> None:
    """Reject private fields and advice/execution wording in calendar responses."""

    forbidden = find_forbidden_keys(value, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    if forbidden:
        raise ValueError(f"economic calendar payload contains forbidden private fields: {sorted(forbidden)}")
    rendered = repr(value).lower()
    for phrase in PROHIBITED_ECONOMIC_CALENDAR_PHRASES:
        if phrase in rendered:
            raise ValueError(f"economic calendar payload contains prohibited wording: {phrase}")


class EconomicCalendarEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    event_reference: str
    event_datetime_utc: str | None = None
    event_has_occurred: bool | None = None
    event_date_label: str
    event_time_label: str
    event_title: str
    event_type: EconomicEventType
    importance: EconomicEventImportance
    importance_source: EconomicEventImportanceSource
    country: str
    currency: str
    actual_label: str | None = None
    forecast_label: str | None = None
    previous_label: str | None = None
    unit_label: str | None = None
    source_label: str
    freshness_label: str
    is_trading_signal: bool
    data_mode: EconomicCalendarDataMode

    @model_validator(mode="after")
    def event_payload_must_be_safe(self) -> "EconomicCalendarEventRead":
        if self.is_trading_signal:
            raise ValueError("economic calendar events must not be trading signals")
        validate_economic_calendar_payload(self.model_dump(mode="python"))
        return self


class EconomicCalendarEventListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    data_mode: EconomicCalendarDataMode
    source_label: str
    as_of_label: str
    freshness_label: str
    window_start: date
    window_end: date
    timezone: str
    importance_source: EconomicEventImportanceSource
    items: tuple[EconomicCalendarEventRead, ...]
    demo_notice: str | None = None
    is_trading_signal: bool
    limitations: tuple[str, ...]

    @model_validator(mode="after")
    def list_payload_must_be_safe(self) -> "EconomicCalendarEventListRead":
        if self.is_trading_signal:
            raise ValueError("economic calendar lists must not be trading signals")
        if any(item.is_trading_signal for item in self.items):
            raise ValueError("economic calendar items must not be trading signals")
        validate_economic_calendar_payload(self.model_dump(mode="python"))
        return self


class EconomicCalendarRefreshStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    status: EconomicCalendarRefreshStatus
    data_mode: EconomicCalendarDataMode
    source_label: str
    as_of_label: str
    imported_at: datetime | None = None
    record_count: int
    message: str

    @model_validator(mode="after")
    def refresh_status_must_be_safe(self) -> "EconomicCalendarRefreshStatusRead":
        validate_economic_calendar_payload(self.model_dump(mode="python"))
        return self
