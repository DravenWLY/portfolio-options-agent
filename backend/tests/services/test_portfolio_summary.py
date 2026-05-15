from datetime import UTC, datetime, date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.cash_balance import CashBalance
from app.models.option_contract import OptionContract
from app.models.option_position import OptionPosition
from app.models.stock_position import StockPosition
from app.models.user import User
from app.services.portfolio.summary import get_portfolio_summary


pytestmark = [pytest.mark.db, pytest.mark.unit]


def _account_with_positions(db_session: Session) -> Account:
    user = User(display_name="Summary Owner")
    db_session.add(user)
    db_session.flush()

    account = Account(
        user_id=user.id,
        broker_name="Demo Broker",
        account_type="taxable_individual",
        display_name="Demo Summary Account",
    )
    db_session.add(account)
    db_session.flush()

    db_session.add(
        CashBalance(
            account_id=account.id,
            total_cash=Decimal("10000.00"),
            reserved_collateral_cash=Decimal("2500.00"),
            free_cash=Decimal("7000.00"),
            premium_income_cash=Decimal("250.00"),
            dca_cash=Decimal("250.00"),
            source="snaptrade",
            data_freshness_status="fresh",
            as_of=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
        )
    )
    db_session.add(
        StockPosition(
            account_id=account.id,
            symbol="VOO",
            asset_type="etf",
            quantity=Decimal("10"),
            market_value=Decimal("4500.00"),
            source="snaptrade",
            data_freshness_status="cached",
            as_of=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
        )
    )
    contract = OptionContract(
        occ_symbol="VOO260116P00400000",
        underlying_symbol="VOO",
        expiration_date=date(2026, 1, 16),
        strike=Decimal("400.0000"),
        option_type="put",
    )
    db_session.add(contract)
    db_session.flush()
    db_session.add(
        OptionPosition(
            account_id=account.id,
            option_contract_id=contract.id,
            position_side="short",
            quantity=Decimal("1"),
            market_value=Decimal("210.00"),
            source="snaptrade",
            data_freshness_status="cached",
            as_of=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
        )
    )
    db_session.commit()
    return account


def test_portfolio_summary_uses_internal_tables(db_session: Session) -> None:
    account = _account_with_positions(db_session)

    summary = get_portfolio_summary(db_session, account.id)

    assert summary is not None
    assert summary.total_cash == Decimal("10000.00")
    assert summary.stock_position_count == 1
    assert summary.stock_market_value == Decimal("4500.00")
    assert summary.option_position_count == 1
    assert summary.short_option_position_count == 1
    assert summary.long_option_position_count == 0
    assert summary.option_market_value == Decimal("-210.00")
    assert summary.total_internal_value == Decimal("14290.00")
    assert summary.data_sources == ["snaptrade"]
    assert summary.data_freshness_statuses == ["cached", "fresh"]
