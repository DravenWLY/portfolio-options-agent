import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


pytestmark = [pytest.mark.api, pytest.mark.db]


def test_create_list_and_get_user(client: TestClient, db_session: Session) -> None:
    response = client.post("/users", json={"display_name": "Demo User", "email": "demo@example.com"})

    assert response.status_code == 201
    created = response.json()
    assert created["display_name"] == "Demo User"
    assert created["email"] == "demo@example.com"

    list_response = client.get("/users")
    assert list_response.status_code == 200
    assert [user["id"] for user in list_response.json()] == [created["id"]]

    get_response = client.get(f"/users/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


def test_get_missing_user_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
