from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


pytestmark = [pytest.mark.api, pytest.mark.unit]


def test_trade_review_preview_returns_sanitized_workspace_contract(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported_flow"] == "stock_buy"
    assert payload["trade_intent_summary"]["symbol"] == "XYZ"
    assert payload["actionability"]["review_actionability_status"] == "manual_confirmation_required"
    assert payload["actionability"]["broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert payload["actionability"]["market_quotes"]["freshness_scope"] == "market_quote"
    assert payload["deterministic_review"]["cash_collateral_impact"]["projected_free_cash_state"] == "not_exposed"
    assert payload["agent_orchestration"] is None
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


@pytest.mark.parametrize(
    ("request_payload", "expected_flow"),
    (
        (
            {
                "supported_flow": "stock_sell_trim",
                "symbol": "XYZ",
                "quantity": "2",
                "price_assumption": "50",
            },
            "stock_sell_trim",
        ),
        (
            {
                "supported_flow": "etf_buy",
                "symbol": "QQQ",
                "quantity": "1",
                "price_assumption": "100",
            },
            "etf_buy",
        ),
        (
            {
                "supported_flow": "etf_sell_trim",
                "symbol": "QQQ",
                "quantity": "1",
                "price_assumption": "100",
            },
            "etf_sell_trim",
        ),
        (
            {
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
            },
            "covered_call",
        ),
    ),
)
def test_trade_review_preview_supports_remaining_phase_18a_flows(
    client: TestClient,
    request_payload: dict,
    expected_flow: str,
) -> None:
    response = client.post("/trade-reviews/preview", json=request_payload)

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported_flow"] == expected_flow
    assert payload["actionability"]["review_actionability_status"] == "manual_confirmation_required"


def test_trade_review_preview_supports_cash_secured_put_with_caveat(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/preview",
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
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported_flow"] == "cash_secured_put"
    assert payload["deterministic_review"]["options_exposure"]["cash_secured_put_collateral_model"] == "generic_rule_only"
    assert "cash_secured_put_collateral_generic" in {caveat["code"] for caveat in payload["caveats"]}


def test_trade_review_preview_rejects_client_supplied_fresh_actionability_metadata(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "broker_snapshot": {
                "source": "snaptrade",
                "freshness_status": "fresh",
                "provider_status": "available",
            },
            "market_quotes": {
                "freshness_status": "fresh",
                "data_mode": "live",
                "actionability_status": "actionable_snapshot",
                "provider_status": "available",
            },
        },
    )

    assert response.status_code == 422


def test_trade_review_preview_rejects_mismatched_shape(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/preview",
        json={
            "supported_flow": "covered_call",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
        },
    )

    assert response.status_code == 422


def test_trade_review_preview_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.post(
        "/trade-reviews/preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("request_payload", "expected_flow"),
    (
        (
            {
                "supported_flow": "stock_buy",
                "symbol": "XYZ",
                "quantity": "3",
                "price_assumption": "50",
            },
            "stock_buy",
        ),
        (
            {
                "supported_flow": "stock_sell_trim",
                "symbol": "XYZ",
                "quantity": "2",
                "price_assumption": "50",
            },
            "stock_sell_trim",
        ),
        (
            {
                "supported_flow": "etf_buy",
                "symbol": "QQQ",
                "quantity": "1",
                "price_assumption": "100",
            },
            "etf_buy",
        ),
        (
            {
                "supported_flow": "etf_sell_trim",
                "symbol": "QQQ",
                "quantity": "1",
                "price_assumption": "100",
            },
            "etf_sell_trim",
        ),
        (
            {
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
            },
            "covered_call",
        ),
        (
            {
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
            },
            "cash_secured_put",
        ),
    ),
)
def test_trade_review_portfolio_preview_supports_allowed_flows(
    client: TestClient,
    request_payload: dict,
    expected_flow: str,
) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            **request_payload,
            "portfolio_context_selection": {"mode": "latest_available"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported_flow"] == expected_flow
    assert payload["portfolio_context"]["context_reference"] == "ctx_demo_latest"
    assert payload["portfolio_context"]["context_source"] == "manual"
    assert payload["portfolio_context"]["stock_position_count"] == 2
    assert payload["portfolio_context"]["option_position_count"] == 1
    assert payload["portfolio_context"]["cash_state"] == "available"
    assert payload["actionability"]["review_actionability_status"] == "manual_confirmation_required"
    assert payload["actionability"]["broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert payload["actionability"]["market_quotes"]["freshness_scope"] == "market_quote"
    assert payload["actionability"]["market_quotes"]["data_mode"] == "manual"
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_preserves_stale_broker_and_market_scopes(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {
                "mode": "selected_context",
                "context_reference": "ctx_demo_stale",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["actionability"]["review_actionability_status"] == "blocked_stale_broker_snapshot"
    assert payload["actionability"]["broker_snapshot"]["freshness_status"] == "stale"
    assert payload["actionability"]["market_quotes"]["freshness_scope"] == "market_quote"
    assert payload["deterministic_review"]["portfolio_impact"]["broker_freshness_status"] == "stale"
    assert "broker_snapshot_stale" in {warning["code"] for warning in payload["deterministic_review"]["missing_data_warnings"]}
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_blocks_unknown_market_freshness(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {
                "mode": "selected_context",
                "context_reference": "ctx_demo_missing",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["portfolio_context"]["context_reference"] == "ctx_demo_missing"
    assert payload["actionability"]["review_actionability_status"] == "blocked_unknown_freshness"
    assert payload["actionability"]["broker_snapshot"]["freshness_status"] == "fresh"
    assert payload["actionability"]["market_quotes"]["freshness_status"] == "unknown"
    assert payload["actionability"]["market_quotes"]["actionability_status"] == "blocked_unknown_quote"
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_handles_no_context_available(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {
                "mode": "selected_context",
                "context_reference": "ctx_demo_empty",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["portfolio_context"] is None
    assert payload["actionability"]["review_actionability_status"] == "blocked_unknown_freshness"
    assert "unknown_freshness" in {warning["code"] for warning in payload["deterministic_review"]["missing_data_warnings"]}
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_trade_review_portfolio_preview_rejects_client_supplied_freshness_metadata(client: TestClient) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {"mode": "latest_available"},
            "broker_snapshot": {"freshness_status": "fresh"},
            "market_quotes": {"data_mode": "live"},
            "actionability": {"review_actionability_status": "normal_review"},
            "cash": "999999",
            "holdings": [{"symbol": "XYZ"}],
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "context_reference",
    (
        "provider_account_id_123",
        "ctx_provider_123",
        "ctx_account_123",
    ),
)
def test_trade_review_portfolio_preview_rejects_non_opaque_context_references(
    client: TestClient,
    context_reference: str,
) -> None:
    response = client.post(
        "/trade-reviews/portfolio-preview",
        json={
            "supported_flow": "stock_buy",
            "symbol": "XYZ",
            "quantity": "3",
            "price_assumption": "50",
            "portfolio_context_selection": {
                "mode": "selected_context",
                "context_reference": context_reference,
            },
        },
    )

    assert response.status_code == 422


def test_user_trade_reviews_returns_sanitized_synthetic_recent_review_list(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/trade-reviews")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"data_mode", "demo_notice", "items"}
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert len(payload["items"]) == 3

    first = payload["items"][0]
    assert first["review_reference"] == "trv_demo_stock_buy_review"
    assert first["supported_flow"] == "stock_buy"
    assert first["review_flow_label"] == "Stock buy review"
    assert first["symbol_or_underlying"] == "XYZ"
    assert first["review_actionability_status"] == "manual_confirmation_required"
    assert first["highest_severity"] == "warning"
    assert first["report_status"] == "preview_only"
    assert first["source_mode"] == "synthetic_preview"
    assert first["broker_snapshot_freshness_label"]
    assert first["market_quote_freshness_label"]
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_trade_reviews_supports_empty_list_state(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/trade-reviews")

    assert response.status_code == 200
    assert response.json() == {
        "data_mode": "synthetic_demo",
        "demo_notice": "demo · not yet connected",
        "items": [],
    }


def test_user_trade_reviews_include_mixed_actionability_and_source_modes(client: TestClient) -> None:
    response = client.get("/users/22222222-2222-2222-2222-222222222222/trade-reviews")

    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["review_actionability_status"] for item in items} == {
        "analysis_only",
        "blocked_unknown_freshness",
        "manual_confirmation_required",
    }
    assert {item["source_mode"] for item in items} == {
        "portfolio_preview",
        "saved_review",
        "synthetic_preview",
    }


def test_user_trade_reviews_do_not_expose_raw_reports_or_private_fields(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/trade-reviews")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "trade_intent_payload",
        "report_body",
        "raw_report",
        "raw_provider_payload",
        "provider_account_id",
        "provider_connection_id",
        "broker_account_id",
        "account_value",
        "buying_power",
        "collateral",
        "threshold",
        "prompt",
        "llm_response",
        "provider_trace",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_trade_reviews_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/trade-reviews")

    assert response.status_code == 401


def test_user_risk_alerts_returns_sanitized_synthetic_alert_list(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/risk-alerts")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"data_mode", "demo_notice", "items"}
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert len(payload["items"]) == 3

    first = payload["items"][0]
    assert first == {
        "alert_reference": "rsk_demo_broker_snapshot_stale",
        "generated_at": first["generated_at"],
        "severity": "blocker",
        "category": "stale_broker_snapshot",
        "title": "Broker snapshot needs review",
        "summary": "Broker snapshot freshness is stale in this demo alert. Confirm portfolio context before relying on account-specific review output.",
        "related_symbol_or_underlying": None,
        "related_review_reference": "trv_demo_covered_call_review",
        "freshness_scope": "broker_snapshot",
        "is_blocking": True,
    }
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_risk_alerts_supports_empty_list_state(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/risk-alerts")

    assert response.status_code == 200
    assert response.json() == {
        "data_mode": "synthetic_demo",
        "demo_notice": "demo · not yet connected",
        "items": [],
    }


def test_user_risk_alerts_preserve_broker_and_market_freshness_separation(client: TestClient) -> None:
    response = client.get("/users/22222222-2222-2222-2222-222222222222/risk-alerts")

    assert response.status_code == 200
    items = response.json()["items"]
    by_category = {item["category"]: item for item in items}
    assert by_category["stale_broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert by_category["stale_broker_snapshot"]["is_blocking"] is True
    assert by_category["stale_market_quote"]["freshness_scope"] == "market_quote"
    assert by_category["stale_market_quote"]["is_blocking"] is False


def test_user_risk_alerts_do_not_expose_raw_thresholds_or_private_fields(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/risk-alerts")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "raw_threshold",
        "threshold_value",
        "allocation_percentage",
        "concentration_percentage",
        "position_quantity",
        "cash_balance",
        "buying_power",
        "account_value",
        "provider_account_id",
        "provider_connection_id",
        "raw_provider_payload",
        "prompt",
        "llm_response",
        "provider_trace",
        "safe to trade",
        "ready to trade",
        "guaranteed",
        "you should",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_risk_alerts_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/risk-alerts")

    assert response.status_code == 401


def test_user_readiness_returns_sanitized_synthetic_summary(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "agent_provider",
        "broker_snapshot",
        "data_mode",
        "demo_notice",
        "generated_at",
        "market_quotes",
        "overall_review_mode",
        "recommended_user_action_label",
    }
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["overall_review_mode"] == "analysis_only"
    assert payload["recommended_user_action_label"] == "Analysis-only: data limitations are present."
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_readiness_preserves_separate_broker_market_and_agent_statuses(client: TestClient) -> None:
    response = client.get("/users/22222222-2222-2222-2222-222222222222/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["broker_snapshot"]["freshness_scope"] == "broker_snapshot"
    assert payload["broker_snapshot"]["status"] == "stale"
    assert payload["broker_snapshot"]["reason_codes"] == ["broker_snapshot_stale"]
    assert payload["broker_snapshot"]["is_blocking"] is True
    assert payload["market_quotes"]["freshness_scope"] == "market_quote"
    assert payload["market_quotes"]["status"] == "manual_review"
    assert payload["market_quotes"]["reason_codes"] == ["market_quote_manual_review"]
    assert payload["market_quotes"]["is_blocking"] is False
    assert payload["agent_provider"]["provider_mode"] == "mock"
    assert payload["agent_provider"]["provider_status"] == "mock_default"
    assert payload["agent_provider"]["is_mock_default"] is True
    assert payload["agent_provider"]["is_blocking"] is False


def test_user_readiness_empty_demo_user_still_carries_demo_metadata(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["overall_review_mode"] in {"analysis_only", "manual_confirmation_required", "blocked", "normal_review"}


def test_user_readiness_avoids_execution_advice_and_private_fields(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/readiness")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "ready_to_trade",
        "safe_to_trade",
        "execution_ready",
        "trade_ready",
        "safe to trade",
        "ready to trade",
        "you should",
        "buy/sell",
        "guaranteed",
        "place order",
        "submit order",
        "execute",
        "raw_holdings",
        "raw_positions",
        "cash_balance",
        "buying_power",
        "account_value",
        "provider_account_id",
        "provider_connection_id",
        "raw_provider_payload",
        "prompt",
        "llm_response",
        "provider_trace",
        "threshold",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_readiness_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/readiness")

    assert response.status_code == 401


def test_user_dashboard_account_summary_returns_sanitized_synthetic_contract(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/dashboard-account-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["summary_reference"] == "das_demo_current"
    assert payload["source_label"] == "Synthetic demo portfolio summary"
    assert payload["portfolio_shape"] == {"stock_position_count": 2, "option_position_count": 1}
    assert payload["cash_state"] == "available"
    assert payload["cash_state_label"] == "Cash state available"
    assert payload["total_value_label"] == "Demo total value · not connected"
    assert payload["cash_label"] == "Demo cash state available · not connected"
    assert payload["stock_exposure_label"] == "Demo stock exposure summary · not connected"
    assert payload["option_exposure_label"] == "Demo option exposure summary · not connected"
    assert "summary_demo_only" in payload["caveat_codes"]
    assert {section["section_key"] for section in payload["display_sections"]} == {
        "freshness",
        "shape",
        "summary",
    }
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_dashboard_account_summary_preserves_broker_and_market_freshness_separation(
    client: TestClient,
) -> None:
    response = client.get("/users/22222222-2222-2222-2222-222222222222/dashboard-account-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert payload["broker_snapshot_freshness"]["status"] == "stale"
    assert payload["broker_snapshot_freshness"]["reason_codes"] == ["broker_snapshot_stale"]
    assert payload["broker_snapshot_freshness"]["is_blocking"] is True
    assert payload["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert payload["market_quote_freshness"]["status"] == "manual_review"
    assert payload["market_quote_freshness"]["reason_codes"] == ["market_quote_manual_review"]
    assert payload["market_quote_freshness"]["is_blocking"] is False
    assert payload["market_data_unavailable"] is False


def test_user_dashboard_account_summary_handles_empty_unavailable_state(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/dashboard-account-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["summary_reference"] == "das_demo_unavailable"
    assert payload["portfolio_shape"] == {"stock_position_count": 0, "option_position_count": 0}
    assert payload["cash_state"] == "unavailable"
    assert payload["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert payload["broker_snapshot_freshness"]["status"] == "unknown"
    assert payload["market_quote_freshness"] is None
    assert payload["market_data_unavailable"] is True
    assert "market_data_unavailable" in payload["caveat_codes"]


def test_user_dashboard_account_summary_avoids_private_fields_and_execution_language(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/dashboard-account-summary")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "raw_holdings",
        "raw_positions",
        "lot",
        "tax_lot",
        "position_quantity",
        "cash_balance",
        "buying_power",
        "account_value",
        "account_id",
        "broker_id",
        "provider_id",
        "provider_account_id",
        "raw_csv",
        "raw_provider_payload",
        "threshold",
        "prompt",
        "llm_response",
        "provider_trace",
        "safe to trade",
        "ready to trade",
        "you should",
        "guaranteed",
        "place order",
        "execute",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_dashboard_account_summary_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/dashboard-account-summary")

    assert response.status_code == 401


def test_user_portfolio_contexts_returns_sanitized_synthetic_context_list(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-contexts")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"data_mode", "demo_notice", "items"}
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert len(payload["items"]) == 3

    first = payload["items"][0]
    assert first["context_reference"] == "ctx_demo_latest"
    assert first["context_label"] == "Latest demo portfolio context"
    assert first["source_kind"] == "manual"
    assert first["portfolio_shape"] == {"stock_position_count": 2, "option_position_count": 1}
    assert first["cash_state"] == "available"
    assert first["cash_state_label"] == "Cash state available"
    assert first["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert first["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert first["market_data_unavailable"] is False
    assert first["actionability_preview"]["review_actionability_status"] == "manual_confirmation_required"
    assert "stock_buy" in first["available_flows"]
    assert "demo_context" in first["caveat_codes"]
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_portfolio_contexts_supports_empty_list_state(client: TestClient) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000000/portfolio-contexts")

    assert response.status_code == 200
    assert response.json() == {
        "data_mode": "synthetic_demo",
        "demo_notice": "demo · not yet connected",
        "items": [],
    }


def test_user_portfolio_context_latest_returns_detail_with_demo_metadata(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/latest")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"data_mode", "demo_notice", "context"}
    assert payload["data_mode"] == "synthetic_demo"
    assert payload["demo_notice"] == "demo · not yet connected"
    assert payload["context"]["context_reference"] == "ctx_demo_latest"
    assert payload["context"]["source_kind"] == "manual"
    assert payload["context"]["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert payload["context"]["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_portfolio_context_detail_preserves_stale_broker_and_market_separation(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/ctx_demo_stale")

    assert response.status_code == 200
    context = response.json()["context"]
    assert context["context_reference"] == "ctx_demo_stale"
    assert context["source_kind"] == "broker_snapshot"
    assert context["broker_snapshot_freshness"]["freshness_scope"] == "broker_snapshot"
    assert context["broker_snapshot_freshness"]["status"] == "stale"
    assert context["broker_snapshot_freshness"]["is_blocking"] is True
    assert context["market_quote_freshness"]["freshness_scope"] == "market_quote"
    assert context["market_quote_freshness"]["status"] == "manual_review"
    assert context["actionability_preview"]["review_actionability_status"] == "blocked_stale_broker_snapshot"
    assert "broker_snapshot_stale" in context["caveat_codes"]


def test_user_portfolio_context_detail_handles_unavailable_market_data(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/ctx_demo_missing")

    assert response.status_code == 200
    context = response.json()["context"]
    assert context["source_kind"] == "csv"
    assert context["market_quote_freshness"] is None
    assert context["market_data_unavailable"] is True
    assert context["actionability_preview"]["review_actionability_status"] == "blocked_unknown_freshness"
    assert "market_data_unavailable" in context["caveat_codes"]


def test_user_portfolio_context_detail_handles_unavailable_context(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/ctx_demo_empty")

    assert response.status_code == 200
    context = response.json()["context"]
    assert context["source_kind"] == "synthetic_demo"
    assert context["portfolio_shape"] == {"stock_position_count": 0, "option_position_count": 0}
    assert context["cash_state"] == "unavailable"
    assert context["market_data_unavailable"] is True
    assert context["available_flows"] == []


def test_user_portfolio_context_detail_returns_not_found_for_unknown_opaque_reference(client: TestClient) -> None:
    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-context/ctx_unknown_123")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "context_reference",
    (
        "provider_account_id_123",
        "ctx_provider_123",
        "ctx_account_123",
        "ctx_cash_12345",
    ),
)
def test_user_portfolio_context_detail_rejects_non_opaque_context_references(
    client: TestClient,
    context_reference: str,
) -> None:
    response = client.get(f"/users/11111111-1111-1111-1111-111111111111/portfolio-context/{context_reference}")

    assert response.status_code == 422


def test_user_portfolio_contexts_do_not_expose_private_fields_or_execution_language(client: TestClient) -> None:
    response = client.get("/users/33333333-3333-3333-3333-333333333333/portfolio-contexts")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    forbidden_text = (
        "raw_holdings",
        "raw_positions",
        "position_quantity",
        "cash_balance",
        "buying_power",
        "account_value",
        "account_id",
        "broker_id",
        "provider_id",
        "provider_account_id",
        "raw_csv",
        "raw_provider_payload",
        "threshold",
        "prompt",
        "llm_response",
        "provider_trace",
        "safe to trade",
        "ready to trade",
        "you should",
        "guaranteed",
        "place order",
        "execute",
    )
    assert not any(text in rendered for text in forbidden_text)
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_user_portfolio_contexts_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/users/11111111-1111-1111-1111-111111111111/portfolio-contexts")

    assert response.status_code == 401
