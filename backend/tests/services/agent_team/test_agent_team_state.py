from datetime import UTC, datetime

import pytest

from app.services.agent_team.state import (
    DEFAULT_AGENT_TEAM_STAGE_ORDER,
    AgentTeamAnalysisState,
    AgentTeamRoleOutput,
    AgentTeamStageStatus,
)


pytestmark = [pytest.mark.unit]


def test_agent_team_stage_order_is_exact() -> None:
    assert DEFAULT_AGENT_TEAM_STAGE_ORDER == (
        "validate_trade_intent",
        "build_deterministic_evidence_bundle",
        "classify_actionability",
        "prepare_public_evidence_context",
        "fundamentals_analyst",
        "news_analyst",
        "technical_analyst",
        "risk_management_agent",
        "portfolio_manager_agent",
        "compose_analysis_console_output",
        "persist_run_steps",
    )


def test_agent_team_state_rejects_private_tokens() -> None:
    with pytest.raises(ValueError, match="private identifier"):
        AgentTeamAnalysisState(
            run_reference="agent-team-test",
            workflow_version="agent-team-analysis-v1",
            generated_at=datetime(2026, 5, 22, tzinfo=UTC),
            review_flow_label="equity_purchase_review",
            review_actionability_status="analysis_only",
            broker_snapshot_freshness={"freshness_status": "fresh"},
            market_quote_freshness={"freshness_status": "manual"},
            deterministic_evidence_summary={"note": "provider_account_id"},
        )


def test_role_output_and_stage_status_are_safe_shapes() -> None:
    output = AgentTeamRoleOutput(
        role_name="news_analyst",
        status="completed",
        content_markdown="Mock analysis-only content.",
        provider_status="ok",
        is_mock=True,
    )
    stage = AgentTeamStageStatus(stage="news_analyst", status="completed", role_name="news_analyst")

    assert output.provider_status == "ok"
    assert stage.stage == "news_analyst"
