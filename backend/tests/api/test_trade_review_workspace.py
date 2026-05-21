from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.services.privacy import FORBIDDEN_PRIVATE_CONTEXT_KEYS, find_forbidden_keys


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
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_PRIVATE_CONTEXT_KEYS | {"provider_contract_id"})


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
