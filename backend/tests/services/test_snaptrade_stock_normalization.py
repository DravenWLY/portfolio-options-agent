from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.user import User
from app.services.broker_import.providers.snaptrade_sdk_client import SnapTradeSDKClient
from app.services.broker_import.normalization.stocks import normalize_stock_position
from app.services.broker_import.providers.models import ProviderPositionSnapshot, ProviderTaxLotSnapshot


pytestmark = [pytest.mark.db, pytest.mark.integration]


def _create_account(db_session: Session) -> Account:
    user = User(display_name="Stock Normalization User")
    db_session.add(user)
    db_session.flush()
    account = Account(
        user_id=user.id,
        broker_name="Fidelity Demo",
        account_type="taxable_individual",
        display_name="Demo Account",
    )
    db_session.add(account)
    db_session.commit()
    return account


def test_snaptrade_stock_position_normalizes_to_internal_snapshot(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    provider_position = ProviderPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        symbol="voo",
        asset_type="etf",
        quantity=Decimal("10"),
        market_value=Decimal("4500.00"),
        currency="USD",
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
        raw_payload={"providerPositionId": "demo-position", "accessToken": "test_secret"},
    )

    position = normalize_stock_position(db_session, account.id, provider_position)
    db_session.commit()

    assert position.account_id == account.id
    assert position.symbol == "VOO"
    assert position.asset_type == "etf"
    assert position.quantity == Decimal("10")
    assert position.market_price is None
    assert position.market_value == Decimal("4500.00")
    assert position.source == "snaptrade"
    assert position.source_ref == "demo-provider-account:VOO"
    assert position.data_freshness_status == "fresh"
    assert position.as_of == timestamp
    assert position.raw_provider_payload == {
        "providerPositionId": "demo-position",
        "accessToken": "[REDACTED]",
    }


def test_snaptrade_stock_position_does_not_treat_provider_market_value_as_quote(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    provider_position = ProviderPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        symbol="QQQ",
        asset_type="etf",
        quantity=Decimal("5"),
        market_value=Decimal("2000.00"),
        currency="USD",
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
        raw_payload={"lastPrice": "400.00"},
    )

    position = normalize_stock_position(db_session, account.id, provider_position)

    assert position.market_value == Decimal("2000.00")
    assert position.market_price is None


def test_snaptrade_stock_position_preserves_broker_reported_enrichment_fields(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    provider_position = ProviderPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        symbol="XYZ",
        asset_type="stock",
        quantity=Decimal("10"),
        market_value=Decimal("550.00"),
        currency="USD",
        instrument_name="Example Holdings Inc.",
        market_price=Decimal("55.00"),
        average_purchase_price=Decimal("40.00"),
        open_pnl=Decimal("150.00"),
        tax_lots=(
            ProviderTaxLotSnapshot(
                acquired_date=datetime(2025, 1, 2, tzinfo=UTC).date(),
                quantity=Decimal("10"),
                purchase_price=Decimal("40.00"),
                cost_basis=Decimal("400.00"),
                current_value=Decimal("550.00"),
                position_type="long",
            ),
        ),
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )

    position = normalize_stock_position(db_session, account.id, provider_position)

    assert position.instrument_name == "Example Holdings Inc."
    assert position.market_price == Decimal("55.00")
    assert position.average_price == Decimal("40.00")
    assert position.cost_basis == Decimal("400.00")
    assert position.open_pnl == Decimal("150.00")
    assert position.currency == "USD"
    assert position.tax_lots == [
        {
            "acquired_date": "2025-01-02",
            "quantity": "10",
            "purchase_price": "40.00",
            "cost_basis": "400.00",
            "current_value": "550.00",
            "position_type": "long",
        }
    ]


def test_snaptrade_sdk_stock_mapping_normalizes_tax_lots_without_raw_lot_ids(db_session: Session) -> None:
    client = SnapTradeSDKClient(snaptrade=object(), db=db_session, encryption_key="test-key")
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)

    mapped = client._map_position(
        {
            "units": "10",
            "price": "55.00",
            "average_purchase_price": "40.00",
            "open_pnl": "150.00",
            "currency": {"code": "USD"},
            "tax_lots": [
                {
                    "original_purchase_date": "2025-01-02T00:00:00Z",
                    "quantity": "10",
                    "purchased_price": "40.00",
                    "cost_basis": "400.00",
                    "current_value": "550.00",
                    "position_type": "LONG",
                    "lot_id": "raw_provider_lot_id_secret",
                }
            ],
            "symbol": {
                "symbol": {
                    "symbol": "XYZ",
                    "description": "Example Holdings Inc.",
                    "type": {"description": "Common Stock"},
                }
            },
        },
        provider_account_id="demo-provider-account",
        now=timestamp,
    )
    snapshot = ProviderPositionSnapshot(**mapped)

    assert snapshot.instrument_name == "Example Holdings Inc."
    assert snapshot.market_price == Decimal("55.00")
    assert snapshot.average_purchase_price == Decimal("40.00")
    assert snapshot.open_pnl == Decimal("150.00")
    assert snapshot.tax_lots[0].acquired_date == datetime(2025, 1, 2, tzinfo=UTC).date()
    assert "raw_provider_lot_id_secret" not in repr(mapped)
