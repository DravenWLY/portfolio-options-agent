from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.schemas.actionability import BrokerSnapshotMetadata, MarketQuotesMetadata, PortfolioActionabilityInput
from app.services.agents import PortfolioContextAgent, ReportHistoryReference
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability
from app.services.trade_review.context import (
    CashContext,
    OptionPositionContext,
    PortfolioReviewContext,
    StockPositionContext,
)


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 20, 16, 0, tzinfo=UTC)


def _context() -> PortfolioReviewContext:
    return PortfolioReviewContext(
        user_id=uuid4(),
        account_id=uuid4(),
        summary_as_of=NOW,
        latest_snapshot_as_of=NOW,
        total_internal_value=Decimal("12345"),
        data_sources=("snaptrade",),
        data_freshness_statuses=("fresh",),
        cash=CashContext(
            total_cash=Decimal("1000"),
            free_cash=Decimal("900"),
            reserved_collateral_cash=Decimal("100"),
            data_freshness_status="fresh",
            as_of=NOW,
            source="snaptrade",
        ),
        stock_positions=(
            StockPositionContext(
                symbol="XYZ",
                asset_type="stock",
                quantity=Decimal("10"),
                market_value=Decimal("1000"),
                data_freshness_status="fresh",
                as_of=NOW,
                source="snaptrade",
            ),
        ),
        option_positions=(
            OptionPositionContext(
                option_contract_id=uuid4(),
                position_side="short",
                quantity=Decimal("1"),
                market_value=Decimal("-120"),
                status="open",
                data_freshness_status="fresh",
                as_of=NOW,
                source="snaptrade",
            ),
        ),
    )


def _actionability(**broker_overrides: object):
    broker_values = {
        "source": "snaptrade",
        "freshness_status": "fresh",
        "sync_status": "succeeded",
        "as_of": NOW,
        "received_at": NOW,
        "last_successful_sync_at": NOW,
        "provider_status": "available",
    }
    broker_values.update(broker_overrides)
    return evaluate_portfolio_snapshot_actionability(
        PortfolioActionabilityInput(
            broker_snapshot=BrokerSnapshotMetadata(**broker_values),
            market_quotes=MarketQuotesMetadata(
                freshness_status="fresh",
                data_mode="live",
                actionability_status="actionable_snapshot",
                as_of_min=NOW,
                as_of_max=NOW,
                received_at_min=NOW,
                received_at_max=NOW,
                provider_status="available",
            ),
        ),
        evaluated_at=NOW,
    )


def test_portfolio_context_agent_returns_structured_deterministic_context() -> None:
    output = PortfolioContextAgent().run(
        portfolio_context=_context(),
        actionability=_actionability(),
        report_history_references=(
            ReportHistoryReference(
                reference_id="report-1",
                report_type="trade_review",
                status="completed",
                created_at=NOW,
            ),
        ),
        generated_at=NOW,
    )

    assert output.agent_name == "portfolio_context_agent"
    assert output.generated_at == NOW
    assert output.portfolio_shape.has_cash_context is True
    assert output.portfolio_shape.stock_position_count == 1
    assert output.portfolio_shape.option_position_count == 1
    assert output.portfolio_shape.short_option_position_count == 1
    assert output.freshness.review_actionability_status == "normal_review"
    assert output.report_history_references[0].reference_id == "report-1"
    payload = output.to_llm_payload()
    assert payload["agent_name"] == "portfolio_context_agent"
    assert "holdings" not in payload
    assert "portfolio_shape" in payload


def test_portfolio_context_agent_reflects_blocked_actionability_without_recomputing() -> None:
    output = PortfolioContextAgent().run(
        portfolio_context=_context(),
        actionability=_actionability(freshness_status="stale"),
        generated_at=NOW,
    )

    assert output.freshness.review_actionability_status == "blocked_stale_broker_snapshot"
    assert output.actionability.can_run_agent_explanation is False
    assert output.notes == ("Context is blocked by the portfolio snapshot actionability policy.",)


def test_portfolio_context_agent_default_payload_excludes_private_broker_data() -> None:
    output = PortfolioContextAgent().run(
        portfolio_context=_context(),
        actionability=_actionability(),
        generated_at=NOW,
    )

    payload = output.to_llm_payload()
    rendered = repr(payload)
    forbidden_keys = FORBIDDEN_REPORT_FACT_KEYS | {
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
        "total_internal_value",
        "total_cash",
        "free_cash",
        "reserved_collateral_cash",
        "market_value",
        "quantity",
    }

    assert forbidden_keys.isdisjoint(_collect_keys(payload))
    assert str(_context().account_id) not in rendered
    assert str(_context().user_id) not in rendered
    assert "12345" not in rendered
    assert "1000" not in rendered
    assert "provider_account_id" not in rendered


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
