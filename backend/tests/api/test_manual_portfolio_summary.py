from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


pytestmark = [pytest.mark.api, pytest.mark.db]


def test_manual_only_portfolio_summary_uses_internal_records_without_broker_sync(
    client: TestClient,
    db_session: Session,
) -> None:
    user_response = client.post("/users", json={"display_name": "Manual Summary Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Manual Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Manual Summary Account",
        },
    )
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]

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
    assert not any(field.startswith(("quote_", "bid_", "ask_", "last_")) for field in payload)
    assert not any("market_quote" in field for field in payload)
