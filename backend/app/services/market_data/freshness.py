from dataclasses import dataclass
from datetime import UTC, datetime

from app.services.market_data.models import (
    ACTIONABILITY_STATUSES,
    DATA_MODES,
    FRESHNESS_STATUSES,
    MARKET_FRESHNESS_SCOPE,
    ActionabilityStatus,
    DataMode,
    FreshnessStatus,
)


DEFAULT_MAX_QUOTE_AGE_SECONDS = 15 * 60


@dataclass(frozen=True)
class QuoteFreshnessDecision:
    freshness_scope: str
    data_mode: DataMode
    freshness_status: FreshnessStatus
    actionability_status: ActionabilityStatus
    quote_age_seconds: int | None
    reason: str


def classify_quote_freshness(
    *,
    data_mode: DataMode,
    quote_time: datetime | None,
    received_at: datetime | None,
    now: datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_QUOTE_AGE_SECONDS,
    provider_error: bool = False,
) -> FreshnessStatus:
    """Classify quote recency, not standalone actionability.

    UI and downstream services must render this together with `data_mode` and
    `actionability_status`. A recent cached or indicative quote may be fresh as
    a snapshot, but still analysis-only because it is not a live actionable
    quote.
    """
    _validate_data_mode(data_mode)
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")
    if provider_error:
        return "error"
    if data_mode == "manual":
        return "manual"
    if data_mode == "eod":
        return "eod_only"
    if data_mode == "unknown":
        return "unknown"

    reference_time = quote_time or received_at
    if reference_time is None:
        return "unknown"

    age_seconds = quote_age_seconds(reference_time, now or datetime.now(UTC))
    if age_seconds > max_age_seconds:
        return "stale"
    if data_mode == "delayed":
        return "delayed"
    return "fresh"


def classify_quote_actionability(
    *,
    data_mode: DataMode,
    freshness_status: FreshnessStatus,
    manual_review_required: bool = False,
    provider_error: bool = False,
) -> ActionabilityStatus:
    _validate_data_mode(data_mode)
    _validate_freshness_status(freshness_status)
    if provider_error or freshness_status == "error":
        return "blocked_provider_error"
    if manual_review_required:
        return "manual_review_required"
    if freshness_status == "stale":
        return "blocked_stale_quote"
    if freshness_status == "unknown":
        return "blocked_unknown_quote"
    if freshness_status in {"manual", "eod_only", "delayed"}:
        return "analysis_only"
    if data_mode == "live" and freshness_status == "fresh":
        return "actionable_snapshot"
    return "analysis_only"


def evaluate_quote_freshness(
    *,
    data_mode: DataMode,
    quote_time: datetime | None,
    received_at: datetime | None,
    now: datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_QUOTE_AGE_SECONDS,
    manual_review_required: bool = False,
    provider_error: bool = False,
) -> QuoteFreshnessDecision:
    evaluation_time = now or datetime.now(UTC)
    freshness_status = classify_quote_freshness(
        data_mode=data_mode,
        quote_time=quote_time,
        received_at=received_at,
        now=evaluation_time,
        max_age_seconds=max_age_seconds,
        provider_error=provider_error,
    )
    actionability_status = classify_quote_actionability(
        data_mode=data_mode,
        freshness_status=freshness_status,
        manual_review_required=manual_review_required,
        provider_error=provider_error,
    )
    reference_time = quote_time or received_at
    age_seconds = quote_age_seconds(reference_time, evaluation_time) if reference_time else None

    return QuoteFreshnessDecision(
        freshness_scope=MARKET_FRESHNESS_SCOPE,
        data_mode=data_mode,
        freshness_status=freshness_status,
        actionability_status=actionability_status,
        quote_age_seconds=age_seconds,
        reason=_decision_reason(data_mode, freshness_status, actionability_status),
    )


def quote_age_seconds(reference_time: datetime, now: datetime) -> int:
    return max(0, int((now - reference_time).total_seconds()))


def _decision_reason(
    data_mode: DataMode,
    freshness_status: FreshnessStatus,
    actionability_status: ActionabilityStatus,
) -> str:
    if actionability_status == "actionable_snapshot":
        return "fresh live market quote snapshot"
    if actionability_status == "blocked_provider_error":
        return "market data provider error"
    if actionability_status == "blocked_stale_quote":
        return "market quote snapshot is stale"
    if actionability_status == "blocked_unknown_quote":
        return "market quote freshness is unknown"
    if actionability_status == "manual_review_required":
        return "market quote requires manual review"
    return f"{data_mode} market quote is for analysis only"


def _validate_data_mode(data_mode: str) -> None:
    if data_mode not in DATA_MODES:
        raise ValueError(f"data_mode must be one of: {', '.join(DATA_MODES)}")


def _validate_freshness_status(freshness_status: str) -> None:
    if freshness_status not in FRESHNESS_STATUSES:
        raise ValueError(f"freshness_status must be one of: {', '.join(FRESHNESS_STATUSES)}")
