from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.user import User
from app.services.broker_import.normalization.cash import normalize_cash_balance
from app.services.broker_import.providers.models import ProviderBalanceSnapshot


pytestmark = [pytest.mark.db, pytest.mark.integration]


def _create_account(db_session: Session) -> Account:
    user = User(display_name="Cash Normalization User")
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


def test_snaptrade_balance_normalizes_to_cash_snapshot(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    balance = ProviderBalanceSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        total_cash=Decimal("10000.00"),
        available_cash=Decimal("7500.00"),
        buying_power=Decimal("12000.00"),
        currency="USD",
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )

    cash = normalize_cash_balance(db_session, account.id, balance)
    db_session.commit()

    assert cash.account_id == account.id
    assert cash.total_cash == Decimal("10000.00")
    assert cash.free_cash == Decimal("7500.00")
    assert cash.reserved_collateral_cash == Decimal("0.00")
    assert cash.source == "snaptrade"
    assert cash.source_ref == "demo-provider-account"
    assert cash.data_freshness_status == "fresh"
    assert cash.as_of == timestamp


def test_snaptrade_balance_uses_total_cash_when_available_cash_missing(db_session: Session) -> None:
    account = _create_account(db_session)
    timestamp = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    balance = ProviderBalanceSnapshot(
        provider="snaptrade",
        provider_account_id="demo-provider-account",
        total_cash=Decimal("10000.00"),
        available_cash=None,
        buying_power=None,
        currency="USD",
        sync_timestamp=timestamp,
        received_at=timestamp,
        sync_status="succeeded",
        data_freshness_status="cached",
    )

    cash = normalize_cash_balance(db_session, account.id, balance)

    assert cash.free_cash == Decimal("10000.00")
    assert cash.data_freshness_status == "cached"
