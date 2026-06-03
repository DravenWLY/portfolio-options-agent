from datetime import UTC, datetime

import pytest

from app.services.agent_team.run_state import (
    AgentReviewBudgetSummary,
    AgentReviewEvalFlag,
    AgentReviewRoleOutput,
    AgentReviewRunState,
    AgentReviewStageStatus,
    AgentReviewTimingSummary,
)


pytestmark = [pytest.mark.unit]


def _baseline(**overrides) -> dict:
    payload = dict(
        run_reference="agent-review-rev_demo",
        workflow_version="agent-review-workflow-v1",
        generated_at=datetime(2026, 5, 23, 15, 30, tzinfo=UTC),
        is_mock=True,
        analysis_only=True,
        review_reference="rev_demo",
        supported_flow="stock_buy",
        review_flow_label="equity_purchase_review",
        review_actionability_status="analysis_only",
        broker_snapshot_freshness={
            "freshness_scope": "broker_snapshot",
            "freshness_status": "fresh",
            "source": "mock",
        },
        market_quote_freshness={
            "freshness_scope": "market_quote",
            "freshness_status": "fresh",
            "data_mode": "mock",
        },
        deterministic_evidence_summary={
            "review_flow_label": "equity_purchase_review",
            "actionability_summary": {"review_actionability_status": "analysis_only", "reason_count": 0},
            "risk_summary": {"has_blocker": False, "risk_rule_count": 0},
            "portfolio_shape": {"context_available": False},
            "caveat_codes": (),
        },
        run_status="completed",
        budget_summary=AgentReviewBudgetSummary(),
        timing_summary=AgentReviewTimingSummary(),
    )
    payload.update(overrides)
    return payload


def test_valid_run_state_constructs() -> None:
    state = AgentReviewRunState(**_baseline())

    assert state.run_reference == "agent-review-rev_demo"
    assert state.run_status == "completed"
    assert state.analysis_only is True
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"


def test_run_state_rejects_forbidden_private_field() -> None:
    summary = {
        "review_flow_label": "equity_purchase_review",
        "cash_balance": "1000.00",  # forbidden private key
    }
    with pytest.raises(ValueError):
        AgentReviewRunState(**_baseline(deterministic_evidence_summary=summary))


def test_run_state_rejects_advice_wording() -> None:
    with pytest.raises(ValueError):
        AgentReviewRunState(**_baseline(final_synthesis="you should buy more of this name now"))


def test_run_state_rejects_invented_metric() -> None:
    with pytest.raises(ValueError):
        AgentReviewRunState(**_baseline(final_synthesis="The expected ROI is 25%."))


def test_run_state_rejects_unknown_run_status() -> None:
    with pytest.raises(ValueError):
        AgentReviewRunState(**_baseline(run_status="definitely_invalid"))


def test_role_output_rejects_invented_metric() -> None:
    with pytest.raises(ValueError):
        AgentReviewRoleOutput(
            role_name="fundamentals_analyst",
            status="completed",
            content_markdown="Price target $123.45 with strong upside.",
            provider_status="ok",
            is_mock=True,
        )


def test_role_output_accepts_safe_mock_text() -> None:
    output = AgentReviewRoleOutput(
        role_name="risk_management_agent",
        status="completed",
        content_markdown="Analysis-only commentary over sanitized deterministic evidence.",
        provider_status="ok",
        is_mock=True,
        latency_ms=3,
    )

    assert output.status == "completed"
    assert output.latency_ms == 3


def test_stage_status_rejects_unknown_outcome() -> None:
    with pytest.raises(ValueError):
        AgentReviewStageStatus(stage="compose_review_narrative", status="bogus_outcome")


def test_stage_status_rejects_negative_latency() -> None:
    with pytest.raises(ValueError):
        AgentReviewStageStatus(stage="fundamentals_analyst", status="completed", latency_ms=-1)


def test_eval_flag_rejects_unknown_status() -> None:
    with pytest.raises(ValueError):
        AgentReviewEvalFlag(check="generated_output_safety", status="bogus")


def test_budget_summary_rejects_negative_tokens() -> None:
    with pytest.raises(ValueError):
        AgentReviewBudgetSummary(tokens_in=-1)
