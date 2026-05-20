from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.schemas.actionability import BrokerSnapshotMetadata, MarketQuotesMetadata, PortfolioActionabilityInput
from app.services.agents import TradeReviewAgent
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS
from app.services.risk.violations import RiskRuleViolation
from app.services.trade_review import (
    AgentSafePortfolioImpact,
    PayoffReview,
    PayoffScenarioPoint,
    TradeReviewAgentProjection,
    TradeReviewMarketSnapshot,
    TradeReviewRiskResult,
    TradeIntentValidationResult,
)
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 20, 17, 0, tzinfo=UTC)


def _projection(*, has_blocker: bool = False) -> TradeReviewAgentProjection:
    return TradeReviewAgentProjection(
        intent_id="intent-1",
        generated_at=NOW,
        calculation_version="trade-review-v1",
        intent_summary={
            "intent_id": "intent-1",
            "asset_class": "stock",
            "intent_type": "stock_review",
            "status": "ready_for_review",
        },
        validation=TradeIntentValidationResult(
            intent_id="intent-1",
            findings=(),
            manual_review_required=False,
            blocked=False,
            highest_severity=None,
            is_clean=True,
        ),
        payoff=PayoffReview(
            intent_id="intent-1",
            asset_class="stock",
            points=(
                PayoffScenarioPoint(
                    label="unchanged",
                    underlying_price=Decimal("100"),
                    net_cash_flow=Decimal("-100"),
                    scenario_value=Decimal("100"),
                    scenario_pnl=Decimal("0"),
                    description="synthetic scenario",
                ),
            ),
            max_loss=None,
            max_gain=None,
            calculation_notes=("Synthetic deterministic scenario.",),
        ),
        portfolio_impact=AgentSafePortfolioImpact(
            broker_freshness_status="fresh",
            market_freshness_status="fresh",
            market_manual_review_required=False,
            assignment_share_delta=Decimal("0"),
            exercise_share_delta=Decimal("0"),
            concentration_symbol="XYZ",
            notes=("Synthetic safe projection.",),
        ),
        risk_rule_violations=(
            (
                RiskRuleViolation(
                    code="synthetic_blocker",
                    severity="blocker",
                    message="Synthetic blocker.",
                    source="test",
                ),
            )
            if has_blocker
            else ()
        ),
        highest_severity="blocker" if has_blocker else None,
        has_blocker=has_blocker,
        data_freshness_snapshot={
            "broker_portfolio_status": "fresh",
            "market_quote_status": "fresh",
        },
        market_snapshot=TradeReviewMarketSnapshot(report_market_snapshot=None),
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


def test_trade_review_agent_explains_deterministic_projection_without_inventing_metrics() -> None:
    output = TradeReviewAgent().run(
        projection=_projection(),
        actionability=_actionability(),
        generated_at=NOW,
    )

    assert output.agent_name == "trade_review_agent"
    assert output.review_actionability_status == "normal_review"
    assert output.can_run_agent_explanation is True
    assert [section.title for section in output.sections] == [
        "Scenario Shape",
        "Risk Findings",
        "Freshness Boundary",
    ]
    assert "payoff.points" in output.deterministic_fields_used
    assert "review_actionability_status" in output.deterministic_fields_used


def test_trade_review_agent_limits_output_when_actionability_blocks_explanation() -> None:
    output = TradeReviewAgent().run(
        projection=_projection(has_blocker=True),
        actionability=_actionability(freshness_status="stale"),
        generated_at=NOW,
    )

    assert output.review_actionability_status == "blocked_stale_broker_snapshot"
    assert output.can_run_agent_explanation is False
    assert output.sections[0].title == "Actionability Gate"
    assert output.deterministic_fields_used == ("review_actionability_status", "actionability.reasons")
    assert "blocks this review" in output.notes[0]


def test_trade_review_agent_payload_avoids_private_fields_and_advice_language() -> None:
    output = TradeReviewAgent().run(
        projection=_projection(),
        actionability=_actionability(),
        generated_at=NOW,
    )
    payload = output.to_llm_payload()
    rendered = repr(payload).lower()
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
        "cash_delta",
        "projected_free_cash",
        "total_cash",
        "free_cash",
        "buying_power",
    }

    assert forbidden.isdisjoint(_collect_keys(payload))
    assert "you should" not in rendered
    assert "recommend buying" not in rendered
    assert "recommend selling" not in rendered
    assert "trade instruction" in rendered


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
