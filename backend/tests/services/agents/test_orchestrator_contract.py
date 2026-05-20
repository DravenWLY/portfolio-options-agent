from datetime import UTC, datetime

import pytest

from app.schemas.actionability import BrokerSnapshotMetadata, MarketQuotesMetadata, PortfolioActionabilityInput
from app.services.agents import (
    ALL_AGENT_ROLES,
    DEFAULT_AGENT_WORKFLOW_STAGES,
    MVP_AGENT_ROLES,
    OPTIONAL_FUTURE_AGENT_ROLES,
    P1_AGENT_ROLES,
    build_orchestration_contract,
    role_registry,
)
from app.services.trade_review.actionability import evaluate_portfolio_snapshot_actionability


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 20, 20, 30, tzinfo=UTC)


def test_default_workflow_stage_order_is_exact() -> None:
    assert DEFAULT_AGENT_WORKFLOW_STAGES == (
        "validate_trade_intent",
        "build_portfolio_context",
        "resolve_market_snapshot",
        "run_deterministic_review",
        "evaluate_actionability",
        "retrieve_public_research_evidence",
        "run_optional_interpretation",
        "run_freshness_guardrail",
        "compose_report",
        "persist_run_steps",
    )
    contract = build_orchestration_contract(run_reference="synthetic-run")

    assert tuple(stage.stage for stage in contract.stages) == DEFAULT_AGENT_WORKFLOW_STAGES


def test_role_vocabulary_is_stable_and_grouped() -> None:
    assert MVP_AGENT_ROLES == (
        "portfolio_context_agent",
        "trade_review_agent",
        "risk_concentration_behavior",
        "freshness_guardrail_agent",
        "report_composer_agent",
    )
    assert P1_AGENT_ROLES == (
        "market_data_agent",
        "news_research_evidence_agent",
        "bull_case_agent",
        "bear_case_agent",
    )
    assert OPTIONAL_FUTURE_AGENT_ROLES == ("tradingagents_public_research_adapter",)
    assert ALL_AGENT_ROLES == MVP_AGENT_ROLES + P1_AGENT_ROLES + OPTIONAL_FUTURE_AGENT_ROLES
    assert tuple(role.role_name for role in role_registry()) == ALL_AGENT_ROLES


def test_actionability_stage_consumes_supplied_policy_decision() -> None:
    decision = _decision()
    contract = build_orchestration_contract(run_reference="synthetic-run", actionability=decision)
    actionability_stage = _stage(contract, "evaluate_actionability")

    assert contract.actionability_status == "normal_review"
    assert actionability_stage.status == "completed"
    assert actionability_stage.execution_mode == "actionability_gate"
    assert actionability_stage.actionability_status == "normal_review"
    assert actionability_stage.source_component == "portfolio_actionability_policy"


def test_blocked_actionability_gates_downstream_interpretation_and_report() -> None:
    decision = _decision(
        broker=BrokerSnapshotMetadata(
            source="snaptrade",
            freshness_status="stale",
            provider_status="available",
        )
    )
    contract = build_orchestration_contract(run_reference="synthetic-run", actionability=decision)

    assert contract.actionability_status == "blocked_stale_broker_snapshot"
    assert _stage(contract, "run_optional_interpretation").status == "gated"
    assert _stage(contract, "compose_report").status == "blocked"
    assert _stage(contract, "compose_report").unavailable_reason == "actionability_policy_blocks_polished_report"
    assert _stage(contract, "run_freshness_guardrail").status == "planned"
    assert _stage(contract, "persist_run_steps").status == "planned"


def test_manual_confirmation_required_gates_report_but_does_not_remove_stage() -> None:
    decision = _decision(broker=BrokerSnapshotMetadata(source="manual", freshness_status="fresh"))
    contract = build_orchestration_contract(run_reference="synthetic-run", actionability=decision)

    assert contract.actionability_status == "manual_confirmation_required"
    assert _stage(contract, "compose_report").status == "gated"
    assert _stage(contract, "compose_report").unavailable_reason == "manual_confirmation_required_before_report_composition"


def test_optional_public_research_tradingagents_llm_and_real_market_provider_are_unavailable_by_default() -> None:
    contract = build_orchestration_contract(run_reference="synthetic-run", actionability=_decision())

    assert _stage(contract, "resolve_market_snapshot").status == "unavailable"
    assert _stage(contract, "resolve_market_snapshot").unavailable_reason == (
        "real_market_provider_not_configured_use_manual_or_mock_snapshot"
    )
    assert _stage(contract, "retrieve_public_research_evidence").status == "unavailable"
    assert _stage(contract, "run_optional_interpretation").status == "unavailable"
    assert _stage(contract, "retrieve_public_research_evidence").role_name == "news_research_evidence_agent"
    assert "tradingagents_public_research_adapter" in ALL_AGENT_ROLES


def test_contract_step_plan_omits_forbidden_private_fields() -> None:
    contract = build_orchestration_contract(run_reference="synthetic-run", actionability=_decision())
    step_plan = contract.to_agent_step_plan()
    rendered = repr(step_plan)

    assert "provider_account_id" not in rendered
    assert "account_id" not in rendered
    assert "cash_balance" not in rendered
    assert "raw_payload" not in rendered
    assert "portal_url" not in rendered


def _decision(*, broker: BrokerSnapshotMetadata | None = None):
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


def _stage(contract, stage_name: str):
    return next(stage for stage in contract.stages if stage.stage == stage_name)
