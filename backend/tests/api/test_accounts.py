import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


pytestmark = [pytest.mark.api, pytest.mark.db]


def _create_user(client: TestClient) -> str:
    response = client.post("/users", json={"display_name": "Account Owner"})
    assert response.status_code == 201
    return response.json()["id"]


def test_create_list_get_update_and_delete_account(client: TestClient, db_session: Session) -> None:
    user_id = _create_user(client)

    create_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Fidelity",
            "account_type": "taxable_individual",
            "display_name": "Demo Taxable",
            "base_currency": "usd",
        },
    )

    assert create_response.status_code == 201
    account = create_response.json()
    assert account["user_id"] == user_id
    assert account["base_currency"] == "USD"

    list_response = client.get(f"/users/{user_id}/accounts")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [account["id"]]

    get_response = client.get(f"/accounts/{account['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["display_name"] == "Demo Taxable"

    patch_response = client.patch(f"/accounts/{account['id']}", json={"display_name": "Updated Taxable"})
    assert patch_response.status_code == 200
    assert patch_response.json()["display_name"] == "Updated Taxable"

    delete_response = client.delete(f"/accounts/{account['id']}")
    assert delete_response.status_code == 204

    hidden_response = client.get(f"/accounts/{account['id']}")
    assert hidden_response.status_code == 404


def test_create_account_for_missing_user_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/users/00000000-0000-0000-0000-000000000001/accounts",
        json={
            "broker_name": "Fidelity",
            "account_type": "taxable_individual",
            "display_name": "Demo Taxable",
        },
    )

    assert response.status_code == 404


def test_account_validation_rejects_invalid_account_type(client: TestClient, db_session: Session) -> None:
    user_id = _create_user(client)

    response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Fidelity",
            "account_type": "unsupported",
            "display_name": "Demo Taxable",
        },
    )

    assert response.status_code == 422
