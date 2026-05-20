from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.actionability import (
    BrokerSnapshotMetadata,
    MarketQuotesMetadata,
    PortfolioActionabilityDecision,
    PortfolioActionabilityInput,
    REVIEW_ACTIONABILITY_STATUSES,
    UserConfirmationMetadata,
)
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 20, 15, 0, tzinfo=UTC)


def _broker(**overrides: object) -> BrokerSnapshotMetadata:
    values = {
        "source": "snaptrade",
        "freshness_status": "fresh",
        "sync_status": "succeeded",
        "as_of": NOW,
        "received_at": NOW,
        "last_successful_sync_at": NOW,
        "provider_status": "available",
    }
    values.update(overrides)
    return BrokerSnapshotMetadata(**values)


def _market(**overrides: object) -> MarketQuotesMetadata:
    values = {
        "freshness_status": "fresh",
        "data_mode": "live",
        "actionability_status": "actionable_snapshot",
        "as_of_min": NOW,
        "as_of_max": NOW,
        "received_at_min": NOW,
        "received_at_max": NOW,
        "provider_status": "available",
    }
    values.update(overrides)
    return MarketQuotesMetadata(**values)


def _decision(
    *,
    broker: BrokerSnapshotMetadata | None = None,
    market: MarketQuotesMetadata | None = None,
    confirmation: UserConfirmationMetadata | None = None,
) -> PortfolioActionabilityDecision:
    return evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=broker or _broker(),
            market_quotes=market or _market(),
            user_confirmation=confirmation,
        ),
        evaluated_at=NOW,
    )


def _confirmed() -> UserConfirmationMetadata:
    return UserConfirmationMetadata(
        state="confirmed",
        confirmed_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=30),
    )


def test_review_actionability_status_catalog_is_exact() -> None:
    assert REVIEW_ACTIONABILITY_STATUSES == (
        "normal_review",
        "analysis_only",
        "manual_confirmation_required",
        "blocked_stale_broker_snapshot",
        "blocked_stale_market_quote",
        "blocked_unknown_freshness",
        "blocked_provider_error",
    )


def test_normal_review_requires_fresh_provider_snapshots() -> None:
    decision = _decision()

    assert decision.review_actionability_status == "normal_review"
    assert decision.can_run_deterministic_review is True
    assert decision.can_run_agent_explanation is True
    assert decision.requires_user_confirmation is False
    assert decision.language_tier == "normal_review"
    assert decision.broker_snapshot.freshness_scope == "broker_snapshot"
    assert decision.market_quotes.freshness_scope == "market_quote"


def test_broker_stale_with_market_fresh_blocks_broker_snapshot() -> None:
    decision = _decision(broker=_broker(freshness_status="stale"))

    assert decision.review_actionability_status == "blocked_stale_broker_snapshot"
    assert decision.can_run_deterministic_review is False
    assert decision.language_tier == "blocked"
    assert decision.reasons[0].scope == "broker_snapshot"


def test_broker_fresh_with_market_stale_blocks_market_quote() -> None:
    decision = _decision(market=_market(freshness_status="stale", actionability_status="blocked_stale_quote"))

    assert decision.review_actionability_status == "blocked_stale_market_quote"
    assert decision.can_run_agent_explanation is False
    assert decision.reasons[0].scope == "market_quote"


@pytest.mark.parametrize("source", ["manual", "csv", "synthetic_mock"])
def test_non_provider_verified_unconfirmed_sources_require_manual_confirmation(source: str) -> None:
    decision = _decision(broker=_broker(source=source))

    assert decision.review_actionability_status == "manual_confirmation_required"
    assert decision.requires_user_confirmation is True
    assert decision.can_run_deterministic_review is False


@pytest.mark.parametrize("source", ["manual", "csv", "synthetic_mock"])
def test_non_provider_verified_confirmed_sources_remain_analysis_only(source: str) -> None:
    decision = _decision(broker=_broker(source=source), confirmation=_confirmed())

    assert decision.review_actionability_status == "analysis_only"
    assert decision.requires_user_confirmation is False
    assert decision.can_run_deterministic_review is True
    assert decision.language_tier == "analysis_only"


@pytest.mark.parametrize(
    ("broker", "market"),
    [
        (_broker(freshness_status="cached"), _market()),
        (_broker(freshness_status="delayed"), _market()),
        (_broker(), _market(data_mode="cached")),
        (_broker(), _market(data_mode="indicative")),
        (_broker(), _market(data_mode="delayed", freshness_status="delayed", actionability_status="analysis_only")),
        (_broker(), _market(data_mode="eod", freshness_status="eod_only", actionability_status="analysis_only")),
        (_broker(), _market(data_mode="manual", freshness_status="manual", actionability_status="manual_review_required")),
    ],
)
def test_cached_delayed_eod_and_manual_inputs_require_confirmation(
    broker: BrokerSnapshotMetadata,
    market: MarketQuotesMetadata,
) -> None:
    unconfirmed = _decision(broker=broker, market=market)
    confirmed = _decision(broker=broker, market=market, confirmation=_confirmed())

    assert unconfirmed.review_actionability_status == "manual_confirmation_required"
    assert confirmed.review_actionability_status == "analysis_only"


def test_provider_error_has_highest_precedence() -> None:
    decision = _decision(
        broker=_broker(freshness_status="stale"),
        market=_market(freshness_status="unknown", provider_status="error"),
    )

    assert decision.review_actionability_status == "blocked_provider_error"
    assert decision.reasons[0].severity == "blocker"


def test_unknown_freshness_precedes_stale_broker_and_market_checks() -> None:
    decision = _decision(
        broker=_broker(freshness_status="stale"),
        market=_market(data_mode="unknown", freshness_status="unknown", actionability_status="blocked_unknown_quote"),
    )

    assert decision.review_actionability_status == "blocked_unknown_freshness"


def test_unknown_provider_status_blocks_for_provider_verified_inputs() -> None:
    decision = _decision(broker=_broker(provider_status="unknown"))

    assert decision.review_actionability_status == "blocked_unknown_freshness"


def test_manual_source_without_provider_status_still_requires_confirmation() -> None:
    decision = _decision(
        broker=BrokerSnapshotMetadata(source="manual", freshness_status="fresh"),
        market=_market(),
    )

    assert decision.review_actionability_status == "manual_confirmation_required"


def test_manual_market_quote_without_provider_status_still_requires_confirmation() -> None:
    decision = _decision(
        broker=_broker(),
        market=MarketQuotesMetadata(
            freshness_status="manual",
            data_mode="manual",
            actionability_status="manual_review_required",
        ),
    )

    assert decision.review_actionability_status == "manual_confirmation_required"


def test_expired_confirmation_does_not_permit_analysis_only() -> None:
    expired = UserConfirmationMetadata(
        state="confirmed",
        confirmed_at=NOW - timedelta(hours=1),
        expires_at=NOW - timedelta(minutes=1),
    )

    decision = _decision(broker=_broker(source="manual"), confirmation=expired)

    assert decision.review_actionability_status == "manual_confirmation_required"


def test_safe_output_shape_omits_forbidden_broker_and_private_fields() -> None:
    forbidden = FORBIDDEN_REPORT_FACT_KEYS | {
        "account_number",
        "broker_account_number",
        "snaptrade_user_id",
        "user_secret",
        "consumer_key",
        "access_token",
        "api_key",
        "portal_url",
        "trade_journal_entries",
        "account_specific_thresholds",
    }
    schemas = [
        BrokerSnapshotMetadata,
        MarketQuotesMetadata,
        UserConfirmationMetadata,
        PortfolioActionabilityInput,
        PortfolioActionabilityDecision,
    ]

    for schema in schemas:
        assert forbidden.isdisjoint(set(schema.model_fields)), schema.__name__

    decision = _decision()
    serialized_keys = _collect_keys(decision.model_dump())

    assert forbidden.isdisjoint(serialized_keys)


def test_actionability_inputs_reject_extra_forbidden_fields() -> None:
    with pytest.raises(ValidationError):
        BrokerSnapshotMetadata(
            source="snaptrade",
            freshness_status="fresh",
            provider_status="available",
            provider_account_id="acct-forbidden",
        )


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        found = set(value)
        for item in value.values():
            found.update(_collect_keys(item))
        return found
    if isinstance(value, (list, tuple)):
        found: set[str] = set()
        for item in value:
            found.update(_collect_keys(item))
        return found
    return set()
