from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.user import User
from app.services.broker_import.providers.models import ProviderAccountSnapshot, ProviderConnectionSnapshot
from app.services.broker_import.refresh_connections import refresh_snaptrade_connections


pytestmark = [pytest.mark.db, pytest.mark.integration]


class FakeSnapTradeConnectionListAdapter:
    def list_connections(self, user_ref: str) -> list[ProviderConnectionSnapshot]:
        now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
        return [
            ProviderConnectionSnapshot(
                provider="snaptrade",
                broker_name="Fidelity Demo",
                provider_connection_id="demo-connection",
                connection_status="connected",
                sync_status="succeeded",
                data_freshness_status="fresh",
                sync_timestamp=now,
                received_at=now,
                warnings=("synthetic warning",),
                raw_payload={"provider_request_id": "demo-request", "userSecret": "should-redact"},
            )
        ]

    def list_accounts(self, connection_ref: str) -> list[ProviderAccountSnapshot]:
        now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
        return [
            ProviderAccountSnapshot(
                provider="snaptrade",
                provider_connection_id=connection_ref,
                provider_account_id="demo-provider-account",
                display_name="Demo Taxable Account",
                account_type="taxable_individual",
                base_currency="USD",
                sync_status="succeeded",
                data_freshness_status="fresh",
                sync_timestamp=now,
                received_at=now,
                raw_payload={"synthetic": True, "userSecret": "should-redact"},
            )
        ]


def _create_user(db_session: Session) -> User:
    user = User(display_name="Refresh Connections User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_refresh_connections_persists_connection_and_account(db_session: Session) -> None:
    user = _create_user(db_session)

    sync_run = refresh_snaptrade_connections(db_session, user.id, FakeSnapTradeConnectionListAdapter())

    connection = db_session.query(BrokerConnection).filter_by(user_id=user.id).one()
    broker_account = db_session.query(BrokerAccount).filter_by(broker_connection_id=connection.id).one()
    account = db_session.get(Account, broker_account.account_id)

    assert sync_run.status == "succeeded"
    assert sync_run.provider_request_id == "demo-request"
    assert sync_run.summary["warnings"] == ["synthetic warning"]
    assert connection.provider_connection_id == "demo-connection"
    assert connection.raw_metadata == {"provider_request_id": "demo-request"}
    assert broker_account.provider_account_id == "demo-provider-account"
    assert broker_account.raw_payload == {"synthetic": True}
    assert account is not None
    assert account.is_manual is False
    assert account.broker_name == "Fidelity Demo"


def test_refresh_connections_reuses_matching_manual_account_without_duplicates(db_session: Session) -> None:
    user = _create_user(db_session)
    manual_account = Account(
        user_id=user.id,
        broker_name="Fidelity Demo",
        account_type="taxable_individual",
        display_name="Manual Taxable Account",
        is_manual=True,
    )
    db_session.add(manual_account)
    db_session.commit()

    refresh_snaptrade_connections(db_session, user.id, FakeSnapTradeConnectionListAdapter())

    accounts = db_session.query(Account).filter_by(user_id=user.id).all()
    broker_account = db_session.query(BrokerAccount).one()
    assert len(accounts) == 1
    assert accounts[0].id == manual_account.id
    assert accounts[0].is_manual is False
    assert broker_account.account_id == manual_account.id
