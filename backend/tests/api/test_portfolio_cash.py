from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


pytestmark = [pytest.mark.api, pytest.mark.db]


def _create_account(client: TestClient) -> str:
    user_response = client.post("/users", json={"display_name": "Cash Snapshot Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Demo Cash Account",
        },
    )
    assert account_response.status_code == 201
    return account_response.json()["id"]


def test_create_and_get_latest_cash_balance(client: TestClient, db_session: Session) -> None:
    account_id = _create_account(client)

    first_response = client.post(
        f"/accounts/{account_id}/cash-balances",
        json={
            "total_cash": "10000.00",
            "reserved_collateral_cash": "2500.00",
            "free_cash": "6000.00",
            "premium_income_cash": "750.00",
            "dca_cash": "750.00",
            "as_of": "2026-05-14T14:00:00Z",
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        f"/accounts/{account_id}/cash-balances",
        json={
            "total_cash": "12000.00",
            "reserved_collateral_cash": "3000.00",
            "free_cash": "7000.00",
            "premium_income_cash": "1000.00",
            "dca_cash": "1000.00",
            "as_of": "2026-05-14T15:00:00Z",
        },
    )
    assert second_response.status_code == 201

    latest_response = client.get(f"/accounts/{account_id}/cash-balances/latest")
    assert latest_response.status_code == 200
    latest = latest_response.json()
    assert latest["account_id"] == account_id
    assert Decimal(latest["total_cash"]) == Decimal("12000.00")
    assert Decimal(latest["reserved_collateral_cash"]) == Decimal("3000.00")


def test_create_cash_balance_for_missing_account_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/accounts/00000000-0000-0000-0000-000000000001/cash-balances",
        json={
            "total_cash": "10000.00",
            "free_cash": "10000.00",
        },
    )

    assert response.status_code == 404


def test_get_latest_cash_balance_for_missing_snapshot_returns_404(client: TestClient, db_session: Session) -> None:
    account_id = _create_account(client)

    response = client.get(f"/accounts/{account_id}/cash-balances/latest")

    assert response.status_code == 404
