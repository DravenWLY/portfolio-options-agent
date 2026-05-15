from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


pytestmark = [pytest.mark.api, pytest.mark.db]


def test_internal_portfolio_storage_flow(client: TestClient, db_session: Session) -> None:
    user_response = client.post("/users", json={"display_name": "Portfolio Flow Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Demo Portfolio Flow",
        },
    )
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]

    cash_response = client.post(
        f"/accounts/{account_id}/cash-balances",
        json={
            "total_cash": "10000.00",
            "reserved_collateral_cash": "2500.00",
            "free_cash": "7000.00",
            "premium_income_cash": "250.00",
            "dca_cash": "250.00",
            "source": "snaptrade",
            "data_freshness_status": "fresh",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert cash_response.status_code == 201

    stock_response = client.post(
        f"/accounts/{account_id}/stock-positions",
        json={
            "symbol": "VOO",
            "asset_type": "etf",
            "quantity": "10.000000",
            "market_value": "4500.00",
            "source": "snaptrade",
            "data_freshness_status": "cached",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert stock_response.status_code == 201

    option_response = client.post(
        f"/accounts/{account_id}/option-positions",
        json={
            "contract": {
                "occ_symbol": "VOO260116P00400000",
                "underlying_symbol": "VOO",
                "expiration_date": "2026-01-16",
                "strike": "400.0000",
                "option_type": "put",
            },
            "position_side": "short",
            "quantity": "1.000000",
            "market_value": "210.00",
            "source": "snaptrade",
            "data_freshness_status": "cached",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert option_response.status_code == 201

    summary_response = client.get(f"/accounts/{account_id}/portfolio")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["cash_as_of"] == "2026-05-14T15:00:00Z"
    assert summary["stock_positions_as_of"] == "2026-05-14T15:00:00Z"
    assert summary["option_positions_as_of"] == "2026-05-14T15:00:00Z"
    assert summary["latest_snapshot_as_of"] == "2026-05-14T15:00:00Z"
    assert Decimal(summary["total_cash"]) == Decimal("10000.00")
    assert summary["stock_position_count"] == 1
    assert Decimal(summary["stock_market_value"]) == Decimal("4500.00")
    assert summary["option_position_count"] == 1
    assert summary["short_option_position_count"] == 1
    assert Decimal(summary["option_market_value"]) == Decimal("-210.00")
    assert Decimal(summary["total_internal_value"]) == Decimal("14290.00")
    assert summary["data_sources"] == ["snaptrade"]
    assert summary["data_freshness_statuses"] == ["cached", "fresh"]
    assert summary["broker_data_warnings"][0]["code"] == "broker_data_cached"
    assert "verify in your broker before manual action" in summary["broker_data_warnings"][0]["message"]
