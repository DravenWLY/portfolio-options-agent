from datetime import UTC, date, datetime
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


pytestmark = [pytest.mark.regression, pytest.mark.db]


def _create_account(db_session: Session) -> Account:
    user = User(display_name="Regression Owner")
    db_session.add(user)
    db_session.flush()

    account = Account(
        user_id=user.id,
        broker_name="Demo Broker",
        account_type="taxable_individual",
        display_name="Regression Account",
    )
    db_session.add(account)
    db_session.flush()

    db_session.add(
        CashBalance(
            account_id=account.id,
            total_cash=Decimal("10000.00"),
            reserved_collateral_cash=Decimal("0.00"),
            free_cash=Decimal("10000.00"),
            premium_income_cash=Decimal("0.00"),
            dca_cash=Decimal("0.00"),
            source="snaptrade",
            data_freshness_status="fresh",
            as_of=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
        )
    )
    db_session.flush()
    return account


def _create_contract(db_session: Session, occ_symbol: str, option_type: str = "put") -> OptionContract:
    contract = OptionContract(
        occ_symbol=occ_symbol,
        underlying_symbol=occ_symbol[:3].strip() or "VOO",
        expiration_date=date(2026, 1, 16),
        strike=Decimal("400.0000"),
        option_type=option_type,
    )
    db_session.add(contract)
    db_session.flush()
    return contract


def test_repeated_stock_snapshots_do_not_double_count(db_session: Session) -> None:
    account = _create_account(db_session)
    db_session.add_all(
        [
            StockPosition(
                account_id=account.id,
                symbol="VOO",
                asset_type="etf",
                quantity=Decimal("10"),
                market_value=Decimal("4400.00"),
                source="snaptrade",
                data_freshness_status="cached",
                as_of=datetime(2026, 5, 14, 14, 0, tzinfo=UTC),
            ),
            StockPosition(
                account_id=account.id,
                symbol="VOO",
                asset_type="etf",
                quantity=Decimal("10"),
                market_value=Decimal("4500.00"),
                source="snaptrade",
                data_freshness_status="fresh",
                as_of=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
            ),
        ]
    )
    db_session.commit()

    summary = get_portfolio_summary(db_session, account.id)

    assert summary is not None
    assert summary.stock_position_count == 1
    assert summary.stock_market_value == Decimal("4500.00")
    assert summary.total_internal_value == Decimal("14500.00")
    assert summary.data_freshness_statuses == ["fresh"]


def test_repeated_option_snapshots_do_not_double_count(db_session: Session) -> None:
    account = _create_account(db_session)
    contract = _create_contract(db_session, "VOO260116P00400000")
    db_session.add_all(
        [
            OptionPosition(
                account_id=account.id,
                option_contract_id=contract.id,
                position_side="short",
                quantity=Decimal("1"),
                market_value=Decimal("300.00"),
                source="snaptrade",
                data_freshness_status="cached",
                as_of=datetime(2026, 5, 14, 14, 0, tzinfo=UTC),
            ),
            OptionPosition(
                account_id=account.id,
                option_contract_id=contract.id,
                position_side="short",
                quantity=Decimal("1"),
                market_value=Decimal("210.00"),
                source="snaptrade",
                data_freshness_status="fresh",
                as_of=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
            ),
        ]
    )
    db_session.commit()

    summary = get_portfolio_summary(db_session, account.id)

    assert summary is not None
    assert summary.option_position_count == 1
    assert summary.short_option_position_count == 1
    assert summary.option_market_value == Decimal("-210.00")
    assert summary.total_internal_value == Decimal("9790.00")
    assert summary.data_freshness_statuses == ["fresh"]


def test_long_and_short_options_use_position_side_signs(db_session: Session) -> None:
    account = _create_account(db_session)
    long_contract = _create_contract(db_session, "QQQ260116C00450000", option_type="call")
    short_contract = _create_contract(db_session, "VOO260116P00400000", option_type="put")
    db_session.add_all(
        [
            OptionPosition(
                account_id=account.id,
                option_contract_id=long_contract.id,
                position_side="long",
                quantity=Decimal("1"),
                market_value=Decimal("125.00"),
                source="snaptrade",
                data_freshness_status="fresh",
                as_of=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
            ),
            OptionPosition(
                account_id=account.id,
                option_contract_id=short_contract.id,
                position_side="short",
                quantity=Decimal("1"),
                market_value=Decimal("210.00"),
                source="snaptrade",
                data_freshness_status="fresh",
                as_of=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
            ),
        ]
    )
    db_session.commit()

    summary = get_portfolio_summary(db_session, account.id)

    assert summary is not None
    assert summary.option_position_count == 2
    assert summary.long_option_position_count == 1
    assert summary.short_option_position_count == 1
    assert summary.option_market_value == Decimal("-85.00")
    assert summary.total_internal_value == Decimal("9915.00")
