from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.schemas.actionability import BrokerSnapshotMetadata, MarketQuotesMetadata, PortfolioActionabilityInput
from app.services.agents import FreshnessGuardrailAgent, PortfolioContextAgent, ReportComposerAgent, TradeReviewAgent
from app.services.privacy import FORBIDDEN_REPORT_FACT_KEYS
from app.services.risk.violations import RiskRuleViolation
from app.services.trade_review import (
    AgentSafePortfolioImpact,
    PayoffReview,
    PayoffScenarioPoint,
    PortfolioReviewContext,
    StockPositionContext,
    TradeReviewAgentProjection,
    TradeReviewMarketSnapshot,
    TradeReviewRiskResult,
    TradeIntentValidationResult,
)
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 20, 19, 0, tzinfo=UTC)


def test_report_composer_builds_traceable_deterministic_markdown() -> None:
    output = _compose()

    assert output.agent_name == "report_composer_agent"
    assert output.markdown.startswith("# Portfolio Trade Review")
    assert "deterministic backend agent outputs only" in output.markdown
    assert "## Portfolio Shape" in output.markdown
    assert "## Freshness Guardrails" in output.markdown
    assert "## Deterministic Trade Review Explanation" in output.markdown
    assert "No LLM-generated sections are included" in output.markdown
    assert "does not recommend, place, route, or manage trades" in output.markdown
    assert output.llm_generated_sections == ()
    assert output.source_agent_names == (
        "portfolio_context_agent",
        "trade_review_agent",
        "freshness_guardrail_agent",
    )


def test_report_composer_creates_report_history_message_payload() -> None:
    output = _compose()

    message = output.to_report_message_create(sequence=7)

    assert message.sender_type == "agent"
    assert message.message_type == "final_report"
    assert message.sequence == 7
    assert message.visibility == "private"
    assert message.content_markdown == output.markdown
    assert message.content_json is not None
    assert message.content_json["generator"] == "report_composer_agent"
    assert message.content_json["llm_generated_sections"] == []
    assert message.content_json["traceability"]["review_actionability_status"] == "normal_review"


def test_report_composer_preserves_blocking_guardrails_in_markdown() -> None:
    output = _compose(
        actionability=_actionability(
            broker=BrokerSnapshotMetadata(
                source="snaptrade",
                freshness_status="stale",
                provider_status="available",
            )
        ),
        projection=_projection(has_blocker=True),
    )

    assert output.traceability["review_actionability_status"] == "blocked_stale_broker_snapshot"
    assert "broker_snapshot/broker_snapshot_stale" in output.markdown
    assert "Has deterministic blocker: True" in output.markdown


def test_report_composer_payload_omits_forbidden_private_fields_and_advice_language() -> None:
    output = _compose()
    message = output.to_report_message_create(sequence=1)
    payload = {
        "output": output._validate_safe() or output.markdown,
        "content_json": message.content_json,
    }
    rendered = repr((output.markdown, message.content_json)).lower()
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
    assert "you should" not in rendered
    assert "recommend buying" not in rendered
    assert "recommend selling" not in rendered
    assert "guaranteed" not in rendered


def _compose(
    *,
    actionability=None,
    projection: TradeReviewAgentProjection | None = None,
):
    actionability = actionability or _actionability()
    portfolio_context = PortfolioContextAgent().run(
        portfolio_context=_portfolio_context(),
        actionability=actionability,
        generated_at=NOW,
    )
    trade_review = TradeReviewAgent().run(
        projection=projection or _projection(),
        actionability=actionability,
        generated_at=NOW,
    )
    guardrail = FreshnessGuardrailAgent().run(
        actionability=actionability,
        generated_at=NOW,
    )
    return ReportComposerAgent().run(
        portfolio_context=portfolio_context,
        trade_review=trade_review,
        freshness_guardrail=guardrail,
        generated_at=NOW,
    )


def _portfolio_context() -> PortfolioReviewContext:
    return PortfolioReviewContext(
        user_id=uuid4(),
        account_id=uuid4(),
        summary_as_of=NOW,
        latest_snapshot_as_of=NOW,
        total_internal_value=Decimal("1200"),
        data_sources=("synthetic",),
        data_freshness_statuses=("fresh",),
        cash=None,
        stock_positions=(
            StockPositionContext(
                symbol="XYZ",
                asset_type="stock",
                quantity=Decimal("3"),
                market_value=Decimal("300"),
                data_freshness_status="fresh",
                as_of=NOW,
                source="synthetic",
            ),
        ),
        option_positions=(),
    )


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


def _actionability(*, broker: BrokerSnapshotMetadata | None = None):
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


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        found = {str(key) for key in value}
        for item in value.values():
            found.update(_collect_keys(item))
        return found
    if isinstance(value, (list, tuple)):
        found: set[str] = set()
        for item in value:
            found.update(_collect_keys(item))
        return found
    return set()
