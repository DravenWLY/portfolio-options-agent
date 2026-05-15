from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection


pytestmark = [pytest.mark.api, pytest.mark.db]


def test_manual_entry_fallback_uses_internal_storage_without_broker_credentials(
    client: TestClient,
    db_session: Session,
) -> None:
    user_response = client.post("/users", json={"display_name": "Manual Entry Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Manual Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Manual Entry Account",
        },
    )
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]

    cash_response = client.post(
        f"/accounts/{account_id}/cash-balances",
        json={
            "total_cash": "7500.00",
            "reserved_collateral_cash": "1500.00",
            "free_cash": "6000.00",
            "premium_income_cash": "125.00",
            "dca_cash": "500.00",
            "source": "manual",
            "data_freshness_status": "unknown",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert cash_response.status_code == 201
    assert cash_response.json()["source"] == "manual"

    stock_response = client.post(
        f"/accounts/{account_id}/stock-positions",
        json={
            "symbol": "DEMO",
            "asset_type": "stock",
            "quantity": "25.000000",
            "market_value": "2500.00",
            "source": "manual",
            "data_freshness_status": "unknown",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert stock_response.status_code == 201
    assert stock_response.json()["source"] == "manual"

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
            "market_value": "100.00",
            "source": "manual",
            "data_freshness_status": "unknown",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert option_response.status_code == 201
    assert option_response.json()["source"] == "manual"

    summary_response = client.get(f"/accounts/{account_id}/portfolio")

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert Decimal(summary["total_cash"]) == Decimal("7500.00")
    assert Decimal(summary["stock_market_value"]) == Decimal("2500.00")
    assert Decimal(summary["option_market_value"]) == Decimal("-100.00")
    assert summary["data_sources"] == ["manual"]
    assert summary["data_freshness_statuses"] == ["unknown"]
    assert [warning["code"] for warning in summary["broker_data_warnings"]] == ["broker_data_unknown"]
    assert db_session.query(BrokerConnection).count() == 0
    assert db_session.query(BrokerAccount).count() == 0
