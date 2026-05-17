from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.stock_position import StockPosition


pytestmark = [pytest.mark.api, pytest.mark.db]


def _create_account(client: TestClient) -> str:
    user_response = client.post("/users", json={"display_name": "Stock Position Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    account_response = client.post(
        f"/users/{user_id}/accounts",
        json={
            "broker_name": "Demo Broker",
            "account_type": "taxable_individual",
            "display_name": "Demo Stock Account",
        },
    )
    assert account_response.status_code == 201
    return account_response.json()["id"]


def test_create_and_list_stock_positions(client: TestClient, db_session: Session) -> None:
    account_id = _create_account(client)

    create_response = client.post(
        f"/accounts/{account_id}/stock-positions",
        json={
            "symbol": "voo",
            "asset_type": "etf",
            "quantity": "10.500000",
            "cost_basis": "4200.00",
            "market_price": "450.1234",
            "market_value": "4726.30",
            "source": "snaptrade",
            "source_ref": "provider_position_demo",
            "data_freshness_status": "cached",
            "raw_provider_payload": {"provider_position_id": "demo_position"},
            "as_of": "2026-05-14T15:00:00Z",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["account_id"] == account_id
    assert created["symbol"] == "VOO"
    assert created["asset_type"] == "etf"
    assert Decimal(created["quantity"]) == Decimal("10.500000")
    assert created["source"] == "snaptrade"
    assert created["data_freshness_status"] == "cached"

    list_response = client.get(f"/accounts/{account_id}/stock-positions")
    assert list_response.status_code == 200
    positions = list_response.json()
    assert [position["id"] for position in positions] == [created["id"]]


def test_create_stock_position_for_missing_account_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/accounts/00000000-0000-0000-0000-000000000001/stock-positions",
        json={
            "symbol": "VOO",
            "quantity": "1.000000",
        },
    )

    assert response.status_code == 404


def test_stock_position_validation_rejects_negative_quantity(client: TestClient, db_session: Session) -> None:
    account_id = _create_account(client)

    response = client.post(
        f"/accounts/{account_id}/stock-positions",
        json={
            "symbol": "VOO",
            "quantity": "-1.000000",
        },
    )

    assert response.status_code == 422


def test_list_stock_positions_tolerates_legacy_provider_rows(client: TestClient, db_session: Session) -> None:
    account_id = _create_account(client)
    db_session.add(
        StockPosition(
            account_id=UUID(account_id),
            symbol="HOOD 85 CALL",
            asset_type="option",
            quantity=Decimal("-1"),
            market_value=Decimal("-290.00"),
            source="snaptrade",
            data_freshness_status="cached",
        )
    )
    db_session.commit()

    response = client.get(f"/accounts/{account_id}/stock-positions")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["symbol"] == "HOOD 85 CALL"
    assert payload[0]["asset_type"] == "option"
    assert Decimal(payload[0]["quantity"]) == Decimal("-1")
    assert Decimal(payload[0]["market_value"]) == Decimal("-290.00")


def test_list_stock_positions_returns_latest_snapshot_per_symbol(
    client: TestClient,
    db_session: Session,
) -> None:
    account_id = _create_account(client)
    account_uuid = UUID(account_id)
    db_session.add_all(
        [
            StockPosition(
                account_id=account_uuid,
                symbol="VOO",
                asset_type="etf",
                quantity=Decimal("66"),
                market_value=Decimal("44800.00"),
                source="snaptrade",
                data_freshness_status="cached",
                as_of=datetime(2026, 5, 17, 17, 0, tzinfo=UTC),
            ),
            StockPosition(
                account_id=account_uuid,
                symbol="VOO",
                asset_type="etf",
                quantity=Decimal("67"),
                market_value=Decimal("45522.48"),
                source="snaptrade",
                data_freshness_status="cached",
                as_of=datetime(2026, 5, 17, 18, 0, tzinfo=UTC),
            ),
            StockPosition(
                account_id=account_uuid,
                symbol="SPAXX",
                asset_type="open_ended_fund",
                quantity=Decimal("43586.25"),
                market_value=Decimal("43586.25"),
                source="snaptrade",
                data_freshness_status="cached",
                as_of=datetime(2026, 5, 17, 18, 0, tzinfo=UTC),
            ),
        ]
    )
    db_session.commit()

    response = client.get(f"/accounts/{account_id}/stock-positions")

    assert response.status_code == 200
    payload = response.json()
    assert [position["symbol"] for position in payload] == ["SPAXX", "VOO"]
    voo = next(position for position in payload if position["symbol"] == "VOO")
    assert Decimal(voo["quantity"]) == Decimal("67")
    assert Decimal(voo["market_value"]) == Decimal("45522.48")
