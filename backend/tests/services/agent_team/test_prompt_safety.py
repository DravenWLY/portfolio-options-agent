from datetime import date

import pytest

from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.legacy_console.evidence import (
    deterministic_evidence_from_workspace,
    public_evidence_from_workspace,
)
from app.services.agent_team.llm_clients.contracts import AGENT_TEAM_ROLES
from app.services.agent_team.legacy_console.prompts import render_role_messages
from app.services.agent_team.agents.roles import PUBLIC_ANALYST_ROLES
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview


pytestmark = [pytest.mark.unit]


def test_each_role_prompt_renders_without_private_context_or_prohibited_phrases() -> None:
    workspace = _workspace()
    public_evidence = public_evidence_from_workspace(workspace)
    deterministic_evidence = deterministic_evidence_from_workspace(workspace)

    for role_name in AGENT_TEAM_ROLES:
        messages = render_role_messages(
            role_name=role_name,
            public_evidence=public_evidence,
            deterministic_evidence=deterministic_evidence if role_name not in PUBLIC_ANALYST_ROLES else None,
            prior_role_summaries=("Synthetic prior analysis-only role output.",),
        )
        rendered = "\n".join(message.content for message in messages).lower()
        assert "provider_account_id" not in rendered
        assert "account_value" not in rendered
        assert "raw_payload" not in rendered
        assert "you should buy" not in rendered
        assert "you should sell" not in rendered
        assert "safe to trade" not in rendered
        assert "ready to trade" not in rendered
        assert "guaranteed return" not in rendered


def test_public_only_roles_do_not_receive_deterministic_portfolio_evidence() -> None:
    workspace = _workspace()
    public_evidence = public_evidence_from_workspace(workspace)

    for role_name in PUBLIC_ANALYST_ROLES:
        messages = render_role_messages(role_name=role_name, public_evidence=public_evidence)
        rendered = "\n".join(message.content for message in messages)
        assert "deterministic_evidence" not in rendered
        assert "portfolio_evidence_allowed': False" in rendered


def test_portfolio_aware_roles_require_sanitized_deterministic_evidence() -> None:
    workspace = _workspace()
    public_evidence = public_evidence_from_workspace(workspace)
    deterministic_evidence = deterministic_evidence_from_workspace(workspace)

    with pytest.raises(ValueError, match="requires deterministic evidence"):
        render_role_messages(role_name="risk_management_agent", public_evidence=public_evidence)

    messages = render_role_messages(
        role_name="risk_management_agent",
        public_evidence=public_evidence,
        deterministic_evidence=deterministic_evidence,
    )
    rendered = "\n".join(message.content for message in messages)
    assert "deterministic_evidence" in rendered
    assert "stock_position_count" in rendered
    assert "option_position_count" in rendered
    assert "cash_balance" not in rendered
    assert "buying_power" not in rendered


def test_prompt_rendering_rejects_private_value_tokens() -> None:
    workspace = _workspace()
    public_evidence = public_evidence_from_workspace(workspace)

    object.__setattr__(public_evidence, "company_name", "Synthetic provider_account_id")
    with pytest.raises(ValueError, match="forbidden private value"):
        render_role_messages(role_name="fundamentals_analyst", public_evidence=public_evidence)


def _workspace():
    return build_trade_review_workspace_portfolio_preview(
        TradeReviewPortfolioPreviewRequest(
            supported_flow="covered_call",
            option_leg={
                "underlying_symbol": "XYZ",
                "option_type": "call",
                "leg_action": "sell_to_open",
                "expiration_date": date(2026, 6, 19),
                "strike": "55",
                "quantity": "1",
                "premium": "2",
            },
            portfolio_context_selection={"mode": "latest_available"},
        )
    )
