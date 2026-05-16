import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.report_message import ReportMessage


pytestmark = [pytest.mark.api, pytest.mark.db]


def test_create_list_and_get_report_thread_detail(client: TestClient, db_session: Session) -> None:
    user_response = client.post("/users", json={"display_name": "Demo Report API", "email": "report-api@example.com"})
    user_id = user_response.json()["id"]

    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Demo Taxable",
            "base_currency": "USD",
        },
    )
    account_id = account_response.json()["id"]

    create_response = client.post(
        f"/users/{user_id}/reports",
        json={
            "account_id": account_id,
            "title": "Synthetic portfolio review",
            "report_type": "portfolio_review",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["user_id"] == user_id
    assert created["account_id"] == account_id
    assert created["title"] == "Synthetic portfolio review"
    assert created["deleted_at"] is None

    db_session.add(
        ReportMessage(
            thread_id=created["id"],
            sender_type="system",
            message_type="markdown_report",
            content_markdown="# Synthetic",
            sequence=1,
        )
    )
    db_session.commit()

    list_response = client.get(f"/users/{user_id}/reports")
    assert list_response.status_code == 200
    assert [thread["id"] for thread in list_response.json()] == [created["id"]]

    detail_response = client.get(f"/users/{user_id}/reports/{created['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == created["id"]
    assert detail["messages"][0]["message_type"] == "markdown_report"
    assert detail["messages"][0]["content_markdown"] == "# Synthetic"


def test_create_report_for_missing_user_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/users/00000000-0000-0000-0000-000000000001/reports",
        json={"title": "Synthetic report"},
    )

    assert response.status_code == 404


def test_create_report_for_account_owned_by_another_user_returns_404(client: TestClient, db_session: Session) -> None:
    owner_response = client.post("/users", json={"display_name": "Owner", "email": "report-owner@example.com"})
    owner_id = owner_response.json()["id"]
    other_response = client.post("/users", json={"display_name": "Other", "email": "report-other@example.com"})
    other_id = other_response.json()["id"]
    account_response = client.post(
        f"/users/{owner_id}/accounts",
        json={
            "broker_name": "Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Owner Account",
            "base_currency": "USD",
        },
    )

    response = client.post(
        f"/users/{other_id}/reports",
        json={"account_id": account_response.json()["id"], "title": "Synthetic report"},
    )

    assert response.status_code == 404


def test_get_report_thread_for_wrong_user_returns_404(client: TestClient, db_session: Session) -> None:
    owner_response = client.post("/users", json={"display_name": "Owner", "email": "detail-owner@example.com"})
    owner_id = owner_response.json()["id"]
    other_response = client.post("/users", json={"display_name": "Other", "email": "detail-other@example.com"})
    other_id = other_response.json()["id"]
    report_response = client.post(f"/users/{owner_id}/reports", json={"title": "Synthetic report"})

    response = client.get(f"/users/{other_id}/reports/{report_response.json()['id']}")

    assert response.status_code == 404
