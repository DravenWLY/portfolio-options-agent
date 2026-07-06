from datetime import UTC, date, datetime

import pytest

from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.legacy_console.evidence import public_evidence_from_workspace
from app.services.agent_team.legacy_console.evidence_projection import build_agent_safe_deterministic_evidence
from app.services.agent_team.llm_clients.contracts import AGENT_TEAM_ROLES, find_forbidden_string_values
from app.services.agent_team.legacy_console.prompt_inputs import build_agent_team_prompt_input, build_all_role_prompt_inputs
from app.services.agent_team.agents.roles import PUBLIC_ANALYST_ROLES
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview


pytestmark = [pytest.mark.unit]


def test_public_roles_do_not_receive_deterministic_portfolio_projection() -> None:
    workspace = _workspace("stock_buy")
    public_evidence = public_evidence_from_workspace(workspace)
    projection = build_agent_safe_deterministic_evidence(workspace)

    for role_name in PUBLIC_ANALYST_ROLES:
        prompt_input = build_agent_team_prompt_input(
            role_name=role_name,
            public_evidence=public_evidence,
            deterministic_evidence=projection,
        )
        snapshot = prompt_input.snapshot()
        assert snapshot["portfolio_evidence_allowed"] is False
        assert snapshot["deterministic_evidence"] is None
        assert find_forbidden_keys(snapshot, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS) == set()
        assert find_forbidden_string_values(snapshot) == set()


def test_risk_and_portfolio_roles_receive_only_agent_safe_projection() -> None:
    workspace = _workspace("covered_call")
    public_evidence = public_evidence_from_workspace(workspace)
    projection = build_agent_safe_deterministic_evidence(workspace)

    risk_input = build_agent_team_prompt_input(
        role_name="risk_management_agent",
        public_evidence=public_evidence,
        deterministic_evidence=projection,
    )
    portfolio_input = build_agent_team_prompt_input(
        role_name="portfolio_manager_agent",
        public_evidence=public_evidence,
        deterministic_evidence=projection,
        prior_role_summaries=("Generic educational text mentioning cash flow without numbers.",),
    )

    assert risk_input.portfolio_evidence_allowed is True
    assert risk_input.deterministic_evidence is not None
    assert risk_input.deterministic_evidence["supported_flow_label"] == "covered_call_review"
    assert portfolio_input.prior_role_summaries == (
        "Prior role output passed output safety but was withheld from strict prompt input.",
    )
    assert find_forbidden_string_values(risk_input.snapshot()) == set()
    assert find_forbidden_string_values(portfolio_input.snapshot()) == set()


def test_all_role_prompt_input_snapshot_is_stable_for_short_put() -> None:
    workspace = _workspace("cash_secured_put")
    prompt_inputs = build_all_role_prompt_inputs(
        role_names=AGENT_TEAM_ROLES,
        public_evidence=public_evidence_from_workspace(workspace),
        deterministic_evidence=build_agent_safe_deterministic_evidence(workspace),
    )
    snapshots = tuple(item.snapshot() for item in prompt_inputs)

    assert tuple(item["role_name"] for item in snapshots) == AGENT_TEAM_ROLES
    assert snapshots[0]["public_context"]["ticker"] == "XYZ"
    assert snapshots[-1]["deterministic_evidence"]["supported_flow_label"] == "short_put_collateral_review"
    rendered = repr(snapshots).lower()
    assert "cash_secured_put" not in rendered
    assert "account_id" not in rendered
    assert "provider_account_id" not in rendered
    assert "raw_payload" not in rendered


def _workspace(flow: str):
    return build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(**_payload(flow)),
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
