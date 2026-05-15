from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.cash_balance import CashBalance
from app.models.option_contract import OptionContract
from app.models.option_position import OptionPosition
from app.models.stock_position import StockPosition
from app.models.user import User
from app.services.broker_import.normalization.cash import normalize_cash_balance
from app.services.broker_import.normalization.options import normalize_option_positions
from app.services.broker_import.normalization.stocks import normalize_stock_positions
from app.services.broker_import.providers.models import (
    ProviderBalanceSnapshot,
    ProviderOptionPositionSnapshot,
    ProviderPositionSnapshot,
)


pytestmark = [pytest.mark.db, pytest.mark.integration]


def _create_account(db_session: Session) -> Account:
    user = User(display_name="Normalization E2E User")
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


def test_snaptrade_normalization_maps_synthetic_payloads_to_internal_tables(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    balance = ProviderBalanceSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        total_cash=Decimal("10000.00"),
        available_cash=Decimal("7500.00"),
        buying_power=Decimal("10000.00"),
        currency="USD",
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )
    stocks = [
        ProviderPositionSnapshot(
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
        ),
        ProviderPositionSnapshot(
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
        ),
    ]
    options = [
        ProviderOptionPositionSnapshot(
            provider="snaptrade",
            provider_account_id="demo-provider-account",
            occ_symbol="VOO260116P00400000",
            underlying_symbol="VOO",
            position_side="short",
            quantity=Decimal("1"),
            market_value=Decimal("210.00"),
            currency="USD",
            sync_timestamp=timestamp,
            received_at=timestamp,
            sync_status="succeeded",
            data_freshness_status="fresh",
        )
    ]

    normalize_cash_balance(db_session, account.id, balance)
    normalize_stock_positions(db_session, account.id, stocks)
    normalize_option_positions(db_session, account.id, options)
    db_session.commit()

    cash_rows = db_session.scalars(select(CashBalance).where(CashBalance.account_id == account.id)).all()
    stock_rows = db_session.scalars(select(StockPosition).where(StockPosition.account_id == account.id)).all()
    option_rows = db_session.scalars(select(OptionPosition).where(OptionPosition.account_id == account.id)).all()
    contracts = db_session.scalars(select(OptionContract)).all()

    assert len(cash_rows) == 1
    assert cash_rows[0].free_cash == Decimal("7500.00")
    assert {row.symbol for row in stock_rows} == {"VOO", "QQQ"}
    assert len(option_rows) == 1
    assert len(contracts) == 1
    assert contracts[0].occ_symbol == "VOO260116P00400000"
    assert all(row.source == "snaptrade" for row in [*cash_rows, *stock_rows, *option_rows])
    assert all(row.data_freshness_status == "fresh" for row in [*cash_rows, *stock_rows, *option_rows])
    assert all(row.as_of == timestamp for row in [*cash_rows, *stock_rows, *option_rows])
