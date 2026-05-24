from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


pytestmark = [pytest.mark.api, pytest.mark.unit]


def test_agent_team_preview_returns_safe_analysis_console(client: TestClient) -> None:
    response = client.post(
        "/agent-team/trade-review-analysis/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_status"] == "completed"
    assert payload["review_flow_label"] == "equity_purchase_review"
    assert payload["review_actionability_status"] == "manual_confirmation_required"
    assert [output["role_name"] for output in payload["role_outputs"]] == [
        "fundamentals_analyst",
        "news_analyst",
        "technical_analyst",
        "risk_management_agent",
        "portfolio_manager_agent",
    ]
    assert payload["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert payload["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert "provider:mock" in payload["safety_flags"]
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_agent_team_preview_supports_option_flow_without_private_fields(client: TestClient) -> None:
    response = client.post(
        "/agent-team/trade-review-analysis/preview",
        json={
            "supported_flow": "cash_secured_put",
            "option_leg": {
                "underlying_symbol": "XYZ",
                "option_type": "put",
                "leg_action": "sell_to_open",
                "expiration_date": str(date(2026, 6, 19)),
                "strike": "50",
                "quantity": "1",
                "premium": "2",
            },
            "portfolio_context_selection": {"mode": "latest_available"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["review_flow_label"] == "short_put_collateral_review"
    rendered = repr(payload).lower()
    assert "provider_account_id" not in rendered
    assert "cash_balance" not in rendered
    assert "you should buy" not in rendered
    assert "ready to trade" not in rendered


def test_agent_team_preview_rejects_client_supplied_prompt_or_provider_metadata(client: TestClient) -> None:
    response = client.post(
        "/agent-team/trade-review-analysis/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
            "prompt": "private",
            "provider": "google",
            "broker_snapshot": {"freshness_status": "fresh"},
        },
    )

    assert response.status_code == 422


def test_agent_team_preview_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.post(
        "/agent-team/trade-review-analysis/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
        },
    )

    assert response.status_code == 401
