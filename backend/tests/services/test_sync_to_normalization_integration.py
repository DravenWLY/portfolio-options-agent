from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.cash_balance import CashBalance
from app.models.option_position import OptionPosition
from app.models.stock_position import StockPosition
from app.models.user import User
from app.services.broker_import.providers.models import (
    ProviderBalanceSnapshot,
    ProviderOptionPositionSnapshot,
    ProviderPositionSnapshot,
    ProviderRefreshResult,
)
from app.services.broker_import.sync import sync_broker_account


pytestmark = [pytest.mark.db, pytest.mark.integration]


class FakeSyncAdapterWithUnsupportedOption:
    def refresh_account(self, provider_account_id: str) -> ProviderRefreshResult:
        now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
        return ProviderRefreshResult(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            status="succeeded",
            started_at=now,
            completed_at=now,
            provider_request_id="demo-refresh",
            accounts_count=1,
        )

    def get_balances(self, provider_account_id: str) -> ProviderBalanceSnapshot:
        now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
        return ProviderBalanceSnapshot(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            total_cash=Decimal("10000.00"),
            available_cash=Decimal("7500.00"),
            buying_power=Decimal("10000.00"),
            currency="USD",
            sync_timestamp=now,
            received_at=now,
            sync_status="succeeded",
            data_freshness_status="fresh",
        )

    def get_positions(self, provider_account_id: str) -> list[ProviderPositionSnapshot]:
        now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
        return [
            ProviderPositionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                symbol="VOO",
                asset_type="etf",
                quantity=Decimal("10"),
                market_value=Decimal("4500.00"),
                currency="USD",
                sync_timestamp=now,
                received_at=now,
                sync_status="succeeded",
                data_freshness_status="fresh",
            )
        ]

    def get_option_positions(self, provider_account_id: str) -> list[ProviderOptionPositionSnapshot]:
        now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
        return [
            ProviderOptionPositionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                occ_symbol="VOO260116P00400000",
                underlying_symbol="VOO",
                position_side="short",
                quantity=Decimal("1"),
                market_value=Decimal("210.00"),
                currency="USD",
                sync_timestamp=now,
                received_at=now,
                sync_status="succeeded",
                data_freshness_status="fresh",
            ),
            ProviderOptionPositionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                occ_symbol="UNSUPPORTED-OPTION",
                underlying_symbol="SPX",
                position_side="long",
                quantity=Decimal("1"),
                market_value=Decimal("50.00"),
                currency="USD",
                sync_timestamp=now,
                received_at=now,
                sync_status="succeeded",
                data_freshness_status="fresh",
            ),
        ]


def _create_broker_account(db_session: Session):
    user = User(display_name="Sync Normalization User")
    db_session.add(user)
    db_session.flush()
    account = Account(
        user_id=user.id,
        broker_name="Fidelity Demo",
        account_type="taxable_individual",
        display_name="Demo Account",
        is_manual=False,
    )
    db_session.add(account)
    db_session.flush()
    connection = BrokerConnection(
        user_id=user.id,
        provider="snaptrade",
        broker_name="Fidelity Demo",
        provider_connection_id="demo-connection",
    )
    db_session.add(connection)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        account_id=account.id,
        provider_account_id="demo-provider-account",
        display_name="Demo Broker Account",
    )
    db_session.add(broker_account)
    db_session.commit()
    db_session.refresh(broker_account)
    return user, account, broker_account


def test_sync_service_populates_internal_tables_and_skips_bad_option(db_session: Session) -> None:
    user, account, broker_account = _create_broker_account(db_session)

    sync_run = sync_broker_account(db_session, user.id, broker_account.id, FakeSyncAdapterWithUnsupportedOption())

    assert sync_run.status == "partially_succeeded"
    assert sync_run.summary["partial_failures"] == [
        {"occ_symbol": "UNSUPPORTED-OPTION", "reason": "unsupported_occ_symbol"}
    ]
    assert db_session.query(CashBalance).filter_by(account_id=account.id).count() == 1
    assert db_session.query(StockPosition).filter_by(account_id=account.id).count() == 1
    assert db_session.query(OptionPosition).filter_by(account_id=account.id).count() == 1
