from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.user import User
from app.services.broker_import.normalization.stocks import normalize_stock_position
from app.services.broker_import.providers.models import ProviderPositionSnapshot


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
