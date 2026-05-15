from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


pytestmark = [pytest.mark.api, pytest.mark.db]

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_csv_preview_fallback_does_not_require_snaptrade_connection(
    client: TestClient,
    db_session: Session,
) -> None:
    user_response = client.post("/users", json={"display_name": "CSV Fallback Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Manual Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "CSV Fallback Account",
        },
    )
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]

    response = client.post(
        f"/accounts/{account_id}/imports/fidelity-csv/preview",
        json={
            "import_type": "positions",
            "csv_text": (FIXTURES_DIR / "fidelity_positions_demo.csv").read_text(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["account_id"] == account_id
    assert payload["provider"] == "fidelity_csv"
    assert payload["mode"] == "preview_only"
    assert payload["import_type"] == "positions"
    assert payload["rows"][0]["data"]["symbol"] == "DEMO"
    assert payload["rows"][0]["data"]["quantity"] == "10"


def test_manual_and_csv_fallback_routes_do_not_require_broker_provider_credentials(
    client: TestClient,
    db_session: Session,
) -> None:
    user_response = client.post("/users", json={"display_name": "Fallback Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Manual Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Fallback Account",
        },
    )
    assert account_response.status_code == 201
    account_id = account_response.json()["id"]

    cash_response = client.post(
        f"/accounts/{account_id}/cash-balances",
        json={
            "total_cash": "1000.00",
            "free_cash": "1000.00",
            "source": "manual",
            "data_freshness_status": "unknown",
        },
    )
    csv_response = client.post(
        f"/accounts/{account_id}/imports/fidelity-csv/preview",
        json={
            "import_type": "transactions",
            "csv_text": (FIXTURES_DIR / "fidelity_transactions_demo.csv").read_text(),
        },
    )

    assert cash_response.status_code == 201
    assert csv_response.status_code == 200
    assert csv_response.json()["rows"][0]["data"]["transaction_id"] == "demo-txn-001"
