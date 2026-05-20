"""Portfolio snapshot actionability policy for trade-review orchestration."""

from datetime import UTC, datetime

from app.schemas.actionability import (
    ActionabilityReason,
    BrokerSnapshotMetadata,
    MarketQuotesMetadata,
    PortfolioActionabilityDecision,
    PortfolioActionabilityInput,
    ReviewActionabilityStatus,
    UserConfirmationMetadata,
)


POLICY_VERSION = "portfolio_actionability_v1"

NON_PROVIDER_VERIFIED_SOURCES = {"manual", "csv", "synthetic_mock"}
BROKER_ANALYSIS_ONLY_STATUSES = {"cached", "delayed"}
MARKET_ANALYSIS_ONLY_FRESHNESS = {"manual", "delayed", "eod_only"}
MARKET_ANALYSIS_ONLY_DATA_MODES = {"cached", "delayed", "indicative", "eod", "manual"}
PROVIDER_ERROR_STATUSES = {"error", "reauth_required", "unavailable"}


def evaluate_portfolio_snapshot_actionability(
    policy_input: PortfolioActionabilityInput,
    *,
    evaluated_at: datetime | None = None,
) -> PortfolioActionabilityDecision:
    """Return one review-level actionability decision with separate freshness metadata."""

    evaluation_time = evaluated_at or datetime.now(UTC)
    broker = policy_input.broker_snapshot
    market = policy_input.market_quotes
    confirmation = policy_input.user_confirmation

    if _has_provider_error(broker, market):
        return _decision(
            "blocked_provider_error",
            evaluation_time=evaluation_time,
            broker=broker,
            market=market,
            confirmation=confirmation,
            reasons=(
                _reason(
                    "provider_error",
                    "review",
                    "blocker",
                    "A required broker or market data provider is unavailable, in error, or requires reauthorization.",
                ),
            ),
        )
    if _has_unknown_freshness(broker, market):
        return _decision(
            "blocked_unknown_freshness",
            evaluation_time=evaluation_time,
            broker=broker,
            market=market,
            confirmation=confirmation,
            reasons=(
                _reason(
                    "unknown_freshness",
                    "review",
                    "blocker",
                    "Required broker snapshot or market quote freshness metadata is unknown.",
                ),
            ),
        )
    if broker.freshness_status == "stale":
        return _decision(
            "blocked_stale_broker_snapshot",
            evaluation_time=evaluation_time,
            broker=broker,
            market=market,
            confirmation=confirmation,
            reasons=(
                _reason(
                    "broker_snapshot_stale",
                    "broker_snapshot",
                    "blocker",
                    "Broker portfolio snapshot is stale for portfolio-aware review.",
                ),
            ),
        )
    if market.freshness_status == "stale" or market.actionability_status == "blocked_stale_quote":
        return _decision(
            "blocked_stale_market_quote",
            evaluation_time=evaluation_time,
            broker=broker,
            market=market,
            confirmation=confirmation,
            reasons=(
                _reason(
                    "market_quote_stale",
                    "market_quote",
                    "blocker",
                    "Required market quote snapshot is stale for portfolio-aware review.",
                ),
            ),
        )
    if _requires_confirmation(broker, market):
        if _confirmation_is_valid(confirmation, evaluation_time):
            return _decision(
                "analysis_only",
                evaluation_time=evaluation_time,
                broker=broker,
                market=market,
                confirmation=confirmation,
                reasons=(
                    _reason(
                        "non_verified_input_confirmed",
                        "review",
                        "warning",
                        "Non-provider-verified or non-live inputs were explicitly confirmed and remain analysis-only.",
                    ),
                ),
            )
        return _decision(
            "manual_confirmation_required",
            evaluation_time=evaluation_time,
            broker=broker,
            market=market,
            confirmation=confirmation,
            reasons=(
                _reason(
                    "manual_confirmation_required",
                    "review",
                    "warning",
                    "Manual, CSV, synthetic/mock, cached, delayed, or EOD inputs require explicit user confirmation.",
                ),
            ),
        )

    return _decision(
        "normal_review",
        evaluation_time=evaluation_time,
        broker=broker,
        market=market,
        confirmation=confirmation,
        reasons=(
            _reason(
                "fresh_provider_snapshots",
                "review",
                "info",
                "Broker snapshot and market quote metadata satisfy the current actionability policy.",
            ),
        ),
    )


def _has_provider_error(broker: BrokerSnapshotMetadata, market: MarketQuotesMetadata) -> bool:
    return (
        broker.freshness_status in {"error", "reauth_required"}
        or broker.provider_status in PROVIDER_ERROR_STATUSES
        or market.freshness_status == "error"
        or market.actionability_status == "blocked_provider_error"
        or market.provider_status in PROVIDER_ERROR_STATUSES
    )


def _has_unknown_freshness(broker: BrokerSnapshotMetadata, market: MarketQuotesMetadata) -> bool:
    return (
        broker.freshness_status == "unknown"
        or (broker.source == "snaptrade" and broker.provider_status == "unknown")
        or market.freshness_status == "unknown"
        or market.data_mode == "unknown"
        or market.actionability_status == "blocked_unknown_quote"
        or (market.data_mode != "manual" and market.provider_status == "unknown")
    )


def _requires_confirmation(broker: BrokerSnapshotMetadata, market: MarketQuotesMetadata) -> bool:
    return (
        broker.source in NON_PROVIDER_VERIFIED_SOURCES
        or broker.freshness_status in BROKER_ANALYSIS_ONLY_STATUSES
        or market.freshness_status in MARKET_ANALYSIS_ONLY_FRESHNESS
        or market.data_mode in MARKET_ANALYSIS_ONLY_DATA_MODES
        or market.actionability_status in {"analysis_only", "manual_review_required"}
    )


def _confirmation_is_valid(confirmation: UserConfirmationMetadata | None, evaluated_at: datetime) -> bool:
    if confirmation is None or confirmation.state != "confirmed":
        return False
    return confirmation.expires_at is None or confirmation.expires_at > evaluated_at


def _decision(
    status: ReviewActionabilityStatus,
    *,
    evaluation_time: datetime,
    broker: BrokerSnapshotMetadata,
    market: MarketQuotesMetadata,
    confirmation: UserConfirmationMetadata | None,
    reasons: tuple[ActionabilityReason, ...],
) -> PortfolioActionabilityDecision:
    blocked = status.startswith("blocked_")
    confirmation_required = status == "manual_confirmation_required"
    runnable = not blocked and not confirmation_required
    return PortfolioActionabilityDecision(
        policy_version=POLICY_VERSION,
        evaluated_at=evaluation_time,
        review_actionability_status=status,
        can_run_deterministic_review=runnable,
        can_run_agent_explanation=runnable,
        requires_user_confirmation=confirmation_required,
        language_tier=_language_tier(status),
        broker_snapshot=broker,
        market_quotes=market,
        reasons=reasons,
        user_confirmation=confirmation,
    )


def _language_tier(status: ReviewActionabilityStatus) -> str:
    if status == "normal_review":
        return "normal_review"
    if status == "analysis_only" or status == "manual_confirmation_required":
        return "analysis_only"
    return "blocked"


def _reason(code: str, scope: str, severity: str, message: str) -> ActionabilityReason:
    return ActionabilityReason(code=code, scope=scope, severity=severity, message=message)
