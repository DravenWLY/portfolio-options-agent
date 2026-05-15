from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.cash_balance import CashBalance
from app.models.stock_position import StockPosition
from app.models.user import User
from app.services.broker_import.normalization.cash import normalize_cash_balance
from app.services.broker_import.normalization.stocks import normalize_stock_position
from app.services.broker_import.providers.models import ProviderBalanceSnapshot, ProviderPositionSnapshot


pytestmark = [pytest.mark.db, pytest.mark.integration]


def _create_account(db_session: Session) -> Account:
    user = User(display_name="Reconciliation User")
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


def test_repeated_cash_snapshot_updates_existing_row(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    balance = ProviderBalanceSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        total_cash=Decimal("10000.00"),
        available_cash=Decimal("7500.00"),
        buying_power=None,
        currency="USD",
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )

    first = normalize_cash_balance(db_session, account.id, balance)
    second = normalize_cash_balance(db_session, account.id, balance)
    db_session.commit()

    rows = db_session.scalars(select(CashBalance).where(CashBalance.account_id == account.id)).all()
    assert first.id == second.id
    assert len(rows) == 1


def test_repeated_stock_snapshot_updates_existing_row(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    provider_position = ProviderPositionSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        symbol="VOO",
        asset_type="etf",
        quantity=Decimal("10"),
        market_value=Decimal("4500.00"),
        currency="USD",
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )

    first = normalize_stock_position(db_session, account.id, provider_position)
    second = normalize_stock_position(db_session, account.id, provider_position)
    db_session.commit()

    rows = db_session.scalars(select(StockPosition).where(StockPosition.account_id == account.id)).all()
    assert first.id == second.id
    assert len(rows) == 1
