from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.schemas.actionability import BrokerSnapshotMetadata, MarketQuotesMetadata, PortfolioActionabilityInput
from app.services.agents import DEFAULT_AGENT_WORKFLOW_STAGES, PortfolioAgentTeamOrchestrator
from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, find_forbidden_keys
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

NOW = datetime(2026, 5, 20, 21, 0, tzinfo=UTC)


def test_orchestrator_runs_deterministic_stage_outputs_in_default_order() -> None:
    result = PortfolioAgentTeamOrchestrator().run(
        run_reference="synthetic-run",
        portfolio_context=_portfolio_context(),
        trade_review_projection=_projection(),
        actionability=_actionability(),
        generated_at=NOW,
    )

    assert tuple(stage.stage for stage in result.stage_outputs) == DEFAULT_AGENT_WORKFLOW_STAGES
    assert result.report_output is not None
    assert result.summary_snapshot()["report_composed"] is True
    assert result.portfolio_context_output.agent_name == "portfolio_context_agent"
    assert result.trade_review_output.agent_name == "trade_review_agent"
    assert result.freshness_guardrail_output.agent_name == "freshness_guardrail_agent"
    assert "report_composer_agent" in result.summary_snapshot()["source_agent_names"]


def test_optional_public_research_market_provider_and_llm_stages_are_unavailable_by_default() -> None:
    result = PortfolioAgentTeamOrchestrator().run(
        run_reference="synthetic-run",
        portfolio_context=_portfolio_context(),
        trade_review_projection=_projection(),
        actionability=_actionability(),
        generated_at=NOW,
    )

    stage_statuses = {stage.stage: stage.status for stage in result.stage_outputs}
    assert stage_statuses["resolve_market_snapshot"] == "unavailable"
    assert stage_statuses["retrieve_public_research_evidence"] == "unavailable"
    assert stage_statuses["run_optional_interpretation"] == "unavailable"
    assert _stage(result, "resolve_market_snapshot").unavailable_reason == (
        "real_market_provider_not_configured_use_manual_or_mock_snapshot"
    )
    assert _stage(result, "retrieve_public_research_evidence").output_envelope is None
    assert _stage(result, "run_optional_interpretation").output_envelope is None


def test_blocked_actionability_runs_guardrail_but_blocks_polished_report() -> None:
    result = PortfolioAgentTeamOrchestrator().run(
        run_reference="synthetic-run",
        portfolio_context=_portfolio_context(),
        trade_review_projection=_projection(has_blocker=True),
        actionability=_actionability(
            broker=BrokerSnapshotMetadata(
                source="snaptrade",
                freshness_status="stale",
                provider_status="available",
            )
        ),
        generated_at=NOW,
    )

    stage_statuses = {stage.stage: stage.status for stage in result.stage_outputs}
    assert result.contract.actionability_status == "blocked_stale_broker_snapshot"
    assert stage_statuses["evaluate_actionability"] == "completed"
    assert stage_statuses["run_freshness_guardrail"] == "completed"
    assert stage_statuses["compose_report"] == "blocked"
    assert stage_statuses["persist_run_steps"] == "completed"
    assert result.report_output is None
    assert result.to_report_message_create(sequence=1) is None


def test_agent_run_step_and_report_message_mapping_are_existing_schema_compatible() -> None:
    result = PortfolioAgentTeamOrchestrator().run(
        run_reference="synthetic-run",
        portfolio_context=_portfolio_context(),
        trade_review_projection=_projection(),
        actionability=_actionability(),
        generated_at=NOW,
    )
    agent_run_id = uuid4()

    run_create = result.to_agent_run_create(account_id=None, report_thread_id=None)
    steps = result.to_agent_step_creates(agent_run_id=agent_run_id)
    message = result.to_report_message_create(sequence=3)

    assert run_create.run_type == "portfolio_agent_team"
    assert run_create.status == "completed"
    assert run_create.provider == "deterministic_backend"
    assert run_create.model is None
    assert run_create.token_budget == 0
    assert run_create.cost_budget == Decimal("0")
    assert run_create.data_freshness_snapshot is not None
    assert run_create.data_freshness_snapshot["broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert run_create.data_freshness_snapshot["market_quotes"]["freshness_scope"] == "market_quote"
    assert len(steps) == len(DEFAULT_AGENT_WORKFLOW_STAGES)
    assert tuple(step.step_order for step in steps) == tuple(range(1, len(DEFAULT_AGENT_WORKFLOW_STAGES) + 1))
    assert steps[0].step_key == "validate_trade_intent"
    assert steps[0].status == "completed"
    assert steps[2].step_key == "resolve_market_snapshot"
    assert steps[2].status == "skipped"
    assert steps[-1].step_key == "persist_run_steps"
    assert steps[-1].output_snapshot_json is not None
    assert steps[-1].output_snapshot_json["payload"]["target_contracts"] == (
        "AgentRunCreate",
        "AgentStepCreate",
        "ReportMessageCreate",
    )
    assert message is not None
    assert message.message_type == "final_report"
    assert message.content_json is not None
    assert message.content_json["generator"] == "report_composer_agent"


def test_blocked_run_maps_to_partially_completed_without_private_fields() -> None:
    result = PortfolioAgentTeamOrchestrator().run(
        run_reference="synthetic-run",
        portfolio_context=_portfolio_context(),
        trade_review_projection=_projection(has_blocker=True),
        actionability=_actionability(
            market=MarketQuotesMetadata(
                freshness_status="stale",
                data_mode="cached",
                actionability_status="blocked_stale_quote",
                provider_status="available",
            )
        ),
        generated_at=NOW,
    )
    run_create = result.to_agent_run_create()
    steps = result.to_agent_step_creates(agent_run_id=uuid4())
    payload = {
        "run_input": run_create.input_snapshot_json,
        "run_output": run_create.output_snapshot_json,
        "run_freshness": run_create.data_freshness_snapshot,
        "step_inputs": [step.input_snapshot_json for step in steps],
        "step_outputs": [step.output_snapshot_json for step in steps],
        "step_freshness": [step.data_freshness_snapshot for step in steps],
        "summary": result.summary_snapshot(),
    }

    assert run_create.status == "partially_completed"
    assert _stage(result, "compose_report").status == "blocked"
    assert result.to_report_message_create(sequence=1) is None
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_PRIVATE_CONTEXT_KEYS)


def test_agent_team_outputs_preserve_broker_and_market_freshness_separation() -> None:
    result = PortfolioAgentTeamOrchestrator().run(
        run_reference="synthetic-run",
        portfolio_context=_portfolio_context(),
        trade_review_projection=_projection(),
        actionability=_actionability(),
        generated_at=NOW,
    )

    freshness = result.data_freshness_snapshot()
    assert freshness["broker_snapshot"] == {
        "freshness_scope": "broker_snapshot",
        "freshness_status": "fresh",
    }
    assert freshness["market_quotes"] == {
        "freshness_scope": "market_quote",
        "freshness_status": "fresh",
    }


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


def _actionability(
    *,
    broker: BrokerSnapshotMetadata | None = None,
    market: MarketQuotesMetadata | None = None,
):
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
        ),
        evaluated_at=NOW,
    )


def _stage(result, stage_name: str):
    return next(stage for stage in result.stage_outputs if stage.stage == stage_name)
