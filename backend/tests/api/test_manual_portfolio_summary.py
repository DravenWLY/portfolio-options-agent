from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


pytestmark = [pytest.mark.api, pytest.mark.db]


def _create_manual_account(client: TestClient, display_name: str = "Manual Summary Account") -> tuple[str, str]:
    user_response = client.post("/users", json={"display_name": f"{display_name} Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Manual Demo Broker",
            "account_type": "taxable_individual",
            "display_name": display_name,
        },
    )
    assert account_response.status_code == 201
    return user_id, account_response.json()["id"]


def test_manual_only_portfolio_summary_uses_internal_records_without_broker_sync(
    client: TestClient,
    db_session: Session,
) -> None:
    _, account_id = _create_manual_account(client)

    cash_response = client.post(
        f"/accounts/{account_id}/cash-balances",
        json={
            "total_cash": "10000.00",
            "reserved_collateral_cash": "1000.00",
            "free_cash": "9000.00",
            "premium_income_cash": "0.00",
            "dca_cash": "0.00",
            "source": "manual",
            "data_freshness_status": "unknown",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert cash_response.status_code == 201
    stock_response = client.post(
        f"/accounts/{account_id}/stock-positions",
        json={
            "symbol": "DEMO",
            "asset_type": "stock",
            "quantity": "10.000000",
            "market_value": "500.00",
            "source": "manual",
            "data_freshness_status": "unknown",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert stock_response.status_code == 201
    option_response = client.post(
        f"/accounts/{account_id}/option-positions",
        json={
            "contract": {
                "occ_symbol": "DEM260116P00040000",
                "underlying_symbol": "DEM",
                "expiration_date": "2026-01-16",
                "strike": "40.0000",
                "option_type": "put",
            },
            "position_side": "short",
            "quantity": "1.000000",
            "market_value": "75.00",
            "source": "manual",
            "data_freshness_status": "unknown",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert option_response.status_code == 201

    response = client.get(f"/accounts/{account_id}/portfolio")

    assert response.status_code == 200
    payload = response.json()
    assert Decimal(payload["total_cash"]) == Decimal("10000.00")
    assert payload["data_sources"] == ["manual"]
    assert payload["data_freshness_statuses"] == ["unknown"]
    assert [warning["code"] for warning in payload["broker_data_warnings"]] == ["broker_data_unknown"]
    assert not any(field.startswith(("quote_", "bid_", "ask_")) for field in payload)
    assert not any("market_quote" in field for field in payload)


def test_manual_only_fresh_portfolio_summary_has_no_broker_data_warnings(
    client: TestClient,
    db_session: Session,
) -> None:
    _, account_id = _create_manual_account(client, "Manual Fresh Summary Account")

    cash_response = client.post(
        f"/accounts/{account_id}/cash-balances",
        json={
            "total_cash": "5000.00",
            "reserved_collateral_cash": "0.00",
            "free_cash": "5000.00",
            "premium_income_cash": "0.00",
            "dca_cash": "0.00",
            "source": "manual",
            "data_freshness_status": "fresh",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    stock_response = client.post(
        f"/accounts/{account_id}/stock-positions",
        json={
            "symbol": "FRESH",
            "asset_type": "stock",
            "quantity": "2.000000",
            "market_value": "200.00",
            "source": "manual",
            "data_freshness_status": "fresh",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    option_response = client.post(
        f"/accounts/{account_id}/option-positions",
        json={
            "contract": {
                "occ_symbol": "FRE260116C00100000",
                "underlying_symbol": "FRE",
                "expiration_date": "2026-01-16",
                "strike": "100.0000",
                "option_type": "call",
            },
            "position_side": "long",
            "quantity": "1.000000",
            "market_value": "25.00",
            "source": "manual",
            "data_freshness_status": "fresh",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert cash_response.status_code == 201
    assert stock_response.status_code == 201
    assert option_response.status_code == 201

    response = client.get(f"/accounts/{account_id}/portfolio")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_sources"] == ["manual"]
    assert payload["data_freshness_statuses"] == ["fresh"]
    assert payload["broker_data_warnings"] == []


def test_empty_manual_account_portfolio_summary_has_stable_zero_shape(
    client: TestClient,
    db_session: Session,
) -> None:
    _, account_id = _create_manual_account(client, "Empty Manual Summary Account")

    response = client.get(f"/accounts/{account_id}/portfolio")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_cash"] == "0"
    assert payload["stock_position_count"] == 0
    assert payload["stock_market_value"] == "0"
    assert payload["option_position_count"] == 0
    assert payload["long_option_position_count"] == 0
    assert payload["short_option_position_count"] == 0
    assert payload["option_market_value"] == "0"
    assert payload["total_internal_value"] == "0"
    assert payload["data_sources"] == []
    assert payload["data_freshness_statuses"] == []
    assert payload["broker_data_warnings"] == []
    assert payload["cash_as_of"] is None
    assert payload["stock_positions_as_of"] is None
    assert payload["option_positions_as_of"] is None
    assert payload["latest_snapshot_as_of"] is None


def test_unknown_freshness_and_missing_market_value_emit_distinct_warning_statuses(
    client: TestClient,
    db_session: Session,
) -> None:
    _, account_id = _create_manual_account(client, "Missing Value Summary Account")
    stock_response = client.post(
        f"/accounts/{account_id}/stock-positions",
        json={
            "symbol": "MISS",
            "asset_type": "stock",
            "quantity": "1.000000",
            "source": "manual",
            "data_freshness_status": "unknown",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert stock_response.status_code == 201

    response = client.get(f"/accounts/{account_id}/portfolio")

    assert response.status_code == 200
    warnings = response.json()["broker_data_warnings"]
    assert {warning["code"] for warning in warnings} == {
        "broker_data_unknown",
        "broker_data_market_value_missing",
    }
    assert {warning["freshness_status"] for warning in warnings} == {"unknown", "not_applicable"}
