from datetime import datetime
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict

from app.schemas.broker_sync_status import DataFreshnessStatus
from app.services.market_data.models import ActionabilityStatus, DataMode, FreshnessStatus


ReviewActionabilityStatus: TypeAlias = Literal[
    "normal_review",
    "analysis_only",
    "manual_confirmation_required",
    "blocked_stale_broker_snapshot",
    "blocked_stale_market_quote",
    "blocked_unknown_freshness",
    "blocked_provider_error",
]
SnapshotSource: TypeAlias = Literal["snaptrade", "manual", "csv", "synthetic_mock"]
ProviderStatus: TypeAlias = Literal["available", "unavailable", "error", "reauth_required", "not_applicable", "unknown"]
ActionabilityReasonScope: TypeAlias = Literal["broker_snapshot", "market_quote", "review"]
ActionabilityReasonSeverity: TypeAlias = Literal["info", "warning", "blocker"]
UserConfirmationState: TypeAlias = Literal["unconfirmed", "confirmed", "expired"]
ActionabilityLanguageTier: TypeAlias = Literal["normal_review", "analysis_only", "blocked"]

REVIEW_ACTIONABILITY_STATUSES: tuple[str, ...] = (
    "normal_review",
    "analysis_only",
    "manual_confirmation_required",
    "blocked_stale_broker_snapshot",
    "blocked_stale_market_quote",
    "blocked_unknown_freshness",
    "blocked_provider_error",
)


class BrokerSnapshotMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    source: SnapshotSource
    freshness_scope: Literal["broker_snapshot"] = "broker_snapshot"
    freshness_status: DataFreshnessStatus
    sync_status: str | None = None
    as_of: datetime | None = None
    received_at: datetime | None = None
    last_successful_sync_at: datetime | None = None
    provider_status: ProviderStatus = "unknown"
    sanitized_error_code: str | None = None
    retryable: bool | None = None


class MarketQuotesMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    freshness_scope: Literal["market_quote"] = "market_quote"
    freshness_status: FreshnessStatus
    data_mode: DataMode
    actionability_status: ActionabilityStatus
    as_of_min: datetime | None = None
    as_of_max: datetime | None = None
    received_at_min: datetime | None = None
    received_at_max: datetime | None = None
    provider_status: ProviderStatus = "unknown"
    sanitized_error_code: str | None = None
    retryable: bool | None = None


class UserConfirmationMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    state: UserConfirmationState = "unconfirmed"
    confirmed_at: datetime | None = None
    expires_at: datetime | None = None
    confirmation_scope: Literal["broker_snapshot", "market_quote", "review"] = "review"


class ActionabilityReason(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    code: str
    scope: ActionabilityReasonScope
    severity: ActionabilityReasonSeverity
    message: str


class PortfolioActionabilityInput(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    broker_snapshot: BrokerSnapshotMetadata
    market_quotes: MarketQuotesMetadata
    user_confirmation: UserConfirmationMetadata | None = None


class PortfolioActionabilityDecision(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    policy_version: str
    evaluated_at: datetime
    review_actionability_status: ReviewActionabilityStatus
    can_run_deterministic_review: bool
    can_run_agent_explanation: bool
    requires_user_confirmation: bool
    language_tier: ActionabilityLanguageTier
    broker_snapshot: BrokerSnapshotMetadata
    market_quotes: MarketQuotesMetadata
    reasons: tuple[ActionabilityReason, ...]
    user_confirmation: UserConfirmationMetadata | None = None
