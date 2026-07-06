from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.services.agent_team.agents.roles import role_definition
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
    # Backend-owned display labels are present and clean (ADR 0009).
    assert [output["display_name"] for output in payload["role_outputs"]] == [
        "Fundamentals Analyst",
        "News Analyst",
        "Technical Analyst",
        "Risk Manager",
        "Portfolio Manager",
    ]
    # Route runs the ReviewRunner spine: provider-neutral synthesis, no "Mock"
    # wording even on the default mock provider (P25A-T15).
    assert payload["final_synthesis"].startswith("Portfolio-team synthesis")
    assert "Mock" not in (payload["final_synthesis"] or "")


def test_agent_team_preview_display_names_match_registry_and_drop_agent_suffix(client: TestClient) -> None:
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

    # role_outputs: display_name matches the backend role registry; machine
    # role_name keys are preserved unchanged; no label contains "Agent".
    for output in payload["role_outputs"]:
        expected = role_definition(output["role_name"]).display_name
        assert output["display_name"] == expected
        assert "Agent" not in output["display_name"]
    assert [output["role_name"] for output in payload["role_outputs"]] == [
        "fundamentals_analyst",
        "news_analyst",
        "technical_analyst",
        "risk_management_agent",
        "portfolio_manager_agent",
    ]

    # stages: display_name is present and registry-matched when role_name is set,
    # and null when role_name is null (deterministic pre/compose/persist stages).
    role_stages = [stage for stage in payload["stages"] if stage["role_name"] is not None]
    non_role_stages = [stage for stage in payload["stages"] if stage["role_name"] is None]
    assert role_stages, "expected role-bound stages"
    for stage in role_stages:
        assert stage["display_name"] == role_definition(stage["role_name"]).display_name
        assert "Agent" not in stage["display_name"]
    assert non_role_stages, "expected deterministic non-role stages"
    assert all(stage["display_name"] is None for stage in non_role_stages)

    # No advice/execution wording or private fields introduced via labels.
    rendered = repr(payload).lower()
    assert "you should buy" not in rendered
    assert "ready to trade" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_agent_team_preview_surfaces_lossy_scope_summary(client: TestClient) -> None:
    response = client.post(
        "/agent-team/trade-review-analysis/preview",
        json={
            "supported_flow": "covered_call",
            "option_leg": {
                "underlying_symbol": "XYZ",
                "option_type": "call",
                "leg_action": "sell_to_open",
                "expiration_date": str(date(2026, 6, 19)),
                "strike": "55",
                "quantity": "1",
                "premium": "2",
            },
            "review_account_selection": {"mode": "selected_account", "account_reference": "acctref_demo_primary"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    scope = payload["scope_summary"]

    # Agent Console states the scope it ran under using lossy categories only:
    # which broader portfolio scope, whether a review account was used, and
    # whether account-level feasibility was evaluated.
    assert scope["review_account_present"] is True
    assert scope["account_level_feasibility_evaluated"] is True
    assert scope["portfolio_scope_mode"] == "selected_context"
    assert "scope_caveat_codes" in scope
    # No account refs, labels, kinds, or other private values leak through.
    rendered = repr(payload).lower()
    assert "acctref_" not in rendered
    assert "primary demo account" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_agent_team_preview_scope_summary_unselected_review_account(client: TestClient) -> None:
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
    scope = response.json()["scope_summary"]
    assert scope["review_account_present"] is False
    assert scope["account_level_feasibility_evaluated"] is False


def test_agent_team_preview_blocked_actionability_degrades_to_deterministic_only(client: TestClient) -> None:
    response = client.post(
        "/agent-team/trade-review-analysis/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "selected_context", "context_reference": "ctx_demo_stale"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    # The ReviewRunner actionability gate is respected through the route: blocked
    # snapshot -> deterministic-only console, no LLM role commentary, safe contract.
    assert payload["review_actionability_status"] == "blocked_stale_broker_snapshot"
    assert payload["role_outputs"] == []
    assert payload["run_status"] == "completed"
    assert "deterministic_only_blocked_actionability" in payload["safety_flags"]
    assert payload["final_synthesis"].startswith("Deterministic-only review")
    assert payload["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
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
