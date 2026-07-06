from datetime import UTC, date, datetime

import pytest

from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.legacy_console.evidence_projection import build_agent_safe_deterministic_evidence
from app.services.agent_team.llm_clients.mock import MockLLMProvider
from app.services.agent_team.legacy_console.orchestrator import AgentTeamOrchestrator
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview


pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    "flow",
    ("stock_buy", "stock_sell_trim", "etf_buy", "etf_sell_trim", "covered_call", "cash_secured_put"),
)
def test_agent_team_scenarios_cover_supported_trade_flows(flow: str) -> None:
    workspace = _workspace(flow)
    projection = build_agent_safe_deterministic_evidence(workspace)
    state = AgentTeamOrchestrator().run(workspace=workspace)

    assert projection.actionability_summary["review_actionability_status"] != "normal_review"
    assert projection.deterministic_metric_source == "backend_owned_not_llm_generated"
    assert state.run_status == "completed"
    assert state.review_actionability_status == workspace.actionability.review_actionability_status
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"
    assert find_forbidden_keys(state.__dict__, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()


@pytest.mark.parametrize(
    ("context_reference", "expected_status"),
    (
        ("ctx_demo_stale", "blocked_stale_broker_snapshot"),
        ("ctx_demo_missing", "blocked_unknown_freshness"),
        ("ctx_demo_empty", "blocked_unknown_freshness"),
    ),
)
def test_agent_team_scenarios_cover_stale_missing_and_blocked_actionability(
    context_reference: str,
    expected_status: str,
) -> None:
    workspace = _workspace("stock_buy", context_reference=context_reference)
    projection = build_agent_safe_deterministic_evidence(workspace)
    state = AgentTeamOrchestrator().run(workspace=workspace)

    assert projection.actionability_summary["review_actionability_status"] == expected_status
    assert projection.missing_stale_data_warnings
    assert state.review_actionability_status == expected_status
    assert state.deterministic_evidence_summary["actionability_summary"]["review_actionability_status"] == expected_status
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"


@pytest.mark.parametrize("failure_status", ("rate_limited", "quota_exceeded"))
def test_agent_team_provider_failures_preserve_deterministic_evidence(failure_status: str) -> None:
    workspace = _workspace("covered_call")
    provider = MockLLMProvider(failure_status_by_role={"news_analyst": failure_status})
    state = AgentTeamOrchestrator(provider=provider).run(workspace=workspace)

    assert state.run_status == "partially_completed"
    assert f"news_analyst:{failure_status}" in state.provider_warnings
    assert state.deterministic_evidence_summary["risk_summary"]["has_blocker"] == workspace.deterministic_review.has_blocker
    assert state.deterministic_evidence_summary["actionability_summary"]["review_actionability_status"] == (
        workspace.actionability.review_actionability_status
    )
    assert state.broker_snapshot_freshness["freshness_scope"] == "broker_snapshot"
    assert state.market_quote_freshness["freshness_scope"] == "market_quote"


def _workspace(flow: str, *, context_reference: str | None = None):
    payload = _payload(flow)
    if context_reference is not None:
        payload["portfolio_context_selection"] = {
            "mode": "selected_context",
            "context_reference": context_reference,
        }
    return build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(**payload),
        generated_at=datetime(2026, 5, 23, 15, 30, tzinfo=UTC),
    )


def _payload(flow: str) -> dict:
    if flow in {"stock_buy", "stock_sell_trim", "etf_buy", "etf_sell_trim"}:
        return {
            "supported_flow": flow,
            "symbol": "XYZ" if flow.startswith("stock") else "QQQ",
            "quantity": "3",
            "price_assumption": "50",
        }
    option_type = "call" if flow == "covered_call" else "put"
    return {
        "supported_flow": flow,
        "option_leg": {
            "underlying_symbol": "XYZ",
            "option_type": option_type,
            "leg_action": "sell_to_open",
            "expiration_date": date(2026, 6, 19),
            "strike": "55" if option_type == "call" else "45",
            "quantity": "1",
            "premium": "2",
        },
    }
