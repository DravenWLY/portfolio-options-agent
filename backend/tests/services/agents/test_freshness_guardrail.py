from datetime import UTC, datetime, timedelta

import pytest

from app.schemas.actionability import (
    BrokerSnapshotMetadata,
    MarketQuotesMetadata,
    PortfolioActionabilityInput,
    UserConfirmationMetadata,
)
from app.services.agents import FreshnessGuardrailAgent
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 20, 18, 0, tzinfo=UTC)


def _decision(*, broker: BrokerSnapshotMetadata | None = None, market: MarketQuotesMetadata | None = None, confirmed: bool = False):
    confirmation = (
        UserConfirmationMetadata(
            state="confirmed",
            confirmed_at=NOW - timedelta(minutes=1),
            expires_at=NOW + timedelta(minutes=30),
        )
        if confirmed
        else None
    )
    return evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=broker
            or BrokerSnapshotMetadata(
                source="snaptrade",
                freshness_status="fresh",
                sync_status="succeeded",
                as_of=NOW,
                received_at=NOW,
                last_successful_sync_at=NOW,
                provider_status="available",
            ),
            market_quotes=market
            or MarketQuotesMetadata(
                freshness_status="fresh",
                data_mode="live",
                actionability_status="actionable_snapshot",
                as_of_min=NOW,
                as_of_max=NOW,
                received_at_min=NOW,
                received_at_max=NOW,
                provider_status="available",
            ),
            user_confirmation=confirmation,
        ),
        evaluated_at=NOW,
    )


def test_guardrail_agent_keeps_broker_and_market_freshness_distinct() -> None:
    output = FreshnessGuardrailAgent().run(actionability=_decision(), generated_at=NOW)

    assert output.review_actionability_status == "normal_review"
    assert output.broker_snapshot_scope == "broker_snapshot"
    assert output.market_quote_scope == "market_quote"
    assert output.broker_snapshot_status == "fresh"
    assert output.market_quote_status == "fresh"
    assert output.guardrails[0].severity == "info"
    assert output.guardrails[0].blocks_agent_explanation is False


def test_stale_broker_snapshot_is_blocking_and_not_immediately_actionable() -> None:
    output = FreshnessGuardrailAgent().run(
        actionability=_decision(
            broker=BrokerSnapshotMetadata(
                source="snaptrade",
                freshness_status="stale",
                provider_status="available",
            )
        ),
        generated_at=NOW,
    )

    assert output.review_actionability_status == "blocked_stale_broker_snapshot"
    assert output.guardrails[0].scope == "broker_snapshot"
    assert output.guardrails[0].severity == "blocker"
    assert output.guardrails[0].blocks_agent_explanation is True
    assert "immediately actionable" in output.guardrails[0].message


def test_stale_market_quote_is_blocking_and_separate_from_broker_snapshot() -> None:
    output = FreshnessGuardrailAgent().run(
        actionability=_decision(
            market=MarketQuotesMetadata(
                freshness_status="stale",
                data_mode="live",
                actionability_status="blocked_stale_quote",
                provider_status="available",
            )
        ),
        generated_at=NOW,
    )

    assert output.review_actionability_status == "blocked_stale_market_quote"
    assert output.guardrails[0].scope == "market_quote"
    assert output.broker_snapshot_status == "fresh"


def test_provider_error_is_blocking_guardrail() -> None:
    output = FreshnessGuardrailAgent().run(
        actionability=_decision(
            market=MarketQuotesMetadata(
                freshness_status="fresh",
                data_mode="live",
                actionability_status="blocked_provider_error",
                provider_status="error",
            )
        ),
        generated_at=NOW,
    )

    assert output.review_actionability_status == "blocked_provider_error"
    assert output.guardrails[0].code == "provider_error"
    assert output.guardrails[0].severity == "blocker"
    assert output.guardrails[0].blocks_agent_explanation is True


def test_unknown_freshness_is_blocking_guardrail() -> None:
    output = FreshnessGuardrailAgent().run(
        actionability=_decision(
            market=MarketQuotesMetadata(
                freshness_status="unknown",
                data_mode="unknown",
                actionability_status="blocked_unknown_quote",
                provider_status="available",
            )
        ),
        generated_at=NOW,
    )

    assert output.review_actionability_status == "blocked_unknown_freshness"
    assert output.guardrails[0].code == "unknown_freshness"
    assert output.guardrails[0].severity == "blocker"


def test_unconfirmed_manual_inputs_require_confirmation_guardrail() -> None:
    output = FreshnessGuardrailAgent().run(
        actionability=_decision(
            broker=BrokerSnapshotMetadata(source="manual", freshness_status="fresh"),
        ),
        generated_at=NOW,
    )

    assert output.review_actionability_status == "manual_confirmation_required"
    assert output.guardrails[0].code == "manual_confirmation_required"
    assert output.guardrails[0].severity == "warning"
    assert output.guardrails[0].blocks_agent_explanation is True


def test_confirmed_manual_inputs_remain_analysis_only() -> None:
    output = FreshnessGuardrailAgent().run(
        actionability=_decision(
            broker=BrokerSnapshotMetadata(source="manual", freshness_status="fresh"),
            confirmed=True,
        ),
        generated_at=NOW,
    )

    assert output.review_actionability_status == "analysis_only"
    assert output.guardrails[0].severity == "warning"
    assert output.guardrails[0].blocks_agent_explanation is False
    assert "analysis" in output.guardrails[0].message


def test_guardrail_agent_step_payload_omits_forbidden_private_fields() -> None:
    output = FreshnessGuardrailAgent().run(actionability=_decision(), generated_at=NOW)
    payload = output.to_agent_step_output()
    forbidden = FORBIDDEN_REPORT_FACT_KEYS | {
        "account_number",
        "broker_account_number",
        "provider_account_id",
        "provider_connection_id",
        "raw_payload",
        "raw_metadata",
        "raw_provider_payload",
        "source_ref",
        "user_secret",
        "consumer_key",
        "access_token",
        "api_key",
        "portal_url",
        "total_cash",
        "free_cash",
        "buying_power",
        "positions",
        "holdings",
    }

    assert forbidden.isdisjoint(_collect_keys(payload))


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
