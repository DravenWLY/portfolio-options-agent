from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.option_position import OptionPosition


pytestmark = [pytest.mark.api, pytest.mark.db]


def _create_account(client: TestClient) -> str:
    user_response = client.post("/users", json={"display_name": "Option Position Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Demo Option Account",
        },
    )
    assert account_response.status_code == 201
    return account_response.json()["id"]


def _option_payload() -> dict:
    return {
        "contract": {
            "occ_symbol": "VOO260116P00400000",
            "underlying_symbol": "VOO",
            "expiration_date": "2026-01-16",
            "strike": "400.0000",
            "option_type": "put",
        },
        "position_side": "short",
        "quantity": "1.000000",
        "average_price": "2.5000",
        "market_price": "2.1000",
        "market_value": "210.00",
        "source": "snaptrade",
        "source_ref": "provider_option_demo",
        "data_freshness_status": "cached",
        "raw_provider_payload": {"provider_position_id": "demo_option_position"},
        "as_of": "2026-05-14T15:00:00Z",
    }


def test_create_and_list_option_positions(client: TestClient, db_session: Session) -> None:
    account_id = _create_account(client)

    create_response = client.post(f"/accounts/{account_id}/option-positions", json=_option_payload())

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["account_id"] == account_id
    assert created["position_side"] == "short"
    assert Decimal(created["quantity"]) == Decimal("1.000000")
    assert created["source"] == "snaptrade"
    assert created["data_freshness_status"] == "cached"

    list_response = client.get(f"/accounts/{account_id}/option-positions")
    assert list_response.status_code == 200
    assert [position["id"] for position in list_response.json()] == [created["id"]]


def test_create_option_position_resolves_contract_idempotently(client: TestClient, db_session: Session) -> None:
    account_id = _create_account(client)

    first_response = client.post(f"/accounts/{account_id}/option-positions", json=_option_payload())
    second_response = client.post(f"/accounts/{account_id}/option-positions", json=_option_payload())

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["option_contract_id"] == second_response.json()["option_contract_id"]


def test_create_option_position_for_missing_account_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/accounts/00000000-0000-0000-0000-000000000001/option-positions",
        json=_option_payload(),
    )

    assert response.status_code == 404


def test_list_option_positions_returns_latest_open_snapshot_per_contract(
    client: TestClient,
    db_session: Session,
) -> None:
    account_id = _create_account(client)
    first_response = client.post(f"/accounts/{account_id}/option-positions", json=_option_payload())
    assert first_response.status_code == 201
    first = first_response.json()
    db_session.add_all(
        [
            OptionPosition(
                account_id=UUID(account_id),
                option_contract_id=UUID(first["option_contract_id"]),
                position_side="short",
                quantity=Decimal("1"),
                average_price=Decimal("2.5000"),
                market_value=Decimal("6.05"),
                status="open",
                source="snaptrade",
                data_freshness_status="cached",
                as_of=datetime(2026, 5, 17, 17, 0, tzinfo=UTC),
            ),
            OptionPosition(
                account_id=UUID(account_id),
                option_contract_id=UUID(first["option_contract_id"]),
                position_side="short",
                quantity=Decimal("1"),
                average_price=Decimal("2.5000"),
                market_value=Decimal("2.90"),
                status="open",
                source="snaptrade",
                data_freshness_status="cached",
                as_of=datetime(2026, 5, 17, 18, 0, tzinfo=UTC),
            ),
        ]
    )
    db_session.commit()

    response = client.get(f"/accounts/{account_id}/option-positions")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert Decimal(payload[0]["market_value"]) == Decimal("2.90")
