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
    account_snapshots: list[ProviderAccountSnapshot] | None = None

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
        if self.account_snapshots is not None:
            return self.account_snapshots
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
        display_name="Demo Taxable Account",
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


def test_refresh_connections_creates_separate_accounts_for_same_broker_and_account_type(
    db_session: Session,
) -> None:
    user = _create_user(db_session)
    now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    adapter = FakeSnapTradeConnectionListAdapter()
    adapter.account_snapshots = [
        ProviderAccountSnapshot(
            provider="snaptrade",
            provider_connection_id="demo-connection",
            provider_account_id="provider-individual",
            display_name="Individual",
            account_type="taxable_individual",
            base_currency="USD",
            sync_status="succeeded",
            data_freshness_status="fresh",
            sync_timestamp=now,
            received_at=now,
        ),
        ProviderAccountSnapshot(
            provider="snaptrade",
            provider_connection_id="demo-connection",
            provider_account_id="provider-cash-management",
            display_name="Cash Management (Individual)",
            account_type="taxable_individual",
            base_currency="USD",
            sync_status="succeeded",
            data_freshness_status="fresh",
            sync_timestamp=now,
            received_at=now,
        ),
    ]

    refresh_snaptrade_connections(db_session, user.id, adapter)

    accounts = db_session.query(Account).filter_by(user_id=user.id).order_by(Account.display_name).all()
    broker_accounts = db_session.query(BrokerAccount).order_by(BrokerAccount.display_name).all()
    assert [account.display_name for account in accounts] == ["Cash Management (Individual)", "Individual"]
    assert len({broker_account.account_id for broker_account in broker_accounts}) == 2


def test_refresh_connections_repairs_shared_internal_account_mapping(
    db_session: Session,
) -> None:
    user = _create_user(db_session)
    now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
    connection = BrokerConnection(
        user_id=user.id,
        provider="snaptrade",
        broker_name="Fidelity Demo",
        provider_connection_id="demo-connection",
    )
    shared_account = Account(
        user_id=user.id,
        broker_name="Fidelity Demo",
        account_type="taxable_individual",
        display_name="Shared Stale Account",
        is_manual=False,
    )
    db_session.add_all([connection, shared_account])
    db_session.flush()
    db_session.add_all(
        [
            BrokerAccount(
                broker_connection_id=connection.id,
                account_id=shared_account.id,
                provider_account_id="provider-individual",
                display_name="Individual",
            ),
            BrokerAccount(
                broker_connection_id=connection.id,
                account_id=shared_account.id,
                provider_account_id="provider-cash-management",
                display_name="Cash Management (Individual)",
            ),
        ]
    )
    db_session.commit()
    adapter = FakeSnapTradeConnectionListAdapter()
    adapter.account_snapshots = [
        ProviderAccountSnapshot(
            provider="snaptrade",
            provider_connection_id="demo-connection",
            provider_account_id="provider-individual",
            display_name="Individual",
            account_type="taxable_individual",
            base_currency="USD",
            sync_status="succeeded",
            data_freshness_status="fresh",
            sync_timestamp=now,
            received_at=now,
        ),
        ProviderAccountSnapshot(
            provider="snaptrade",
            provider_connection_id="demo-connection",
            provider_account_id="provider-cash-management",
            display_name="Cash Management (Individual)",
            account_type="taxable_individual",
            base_currency="USD",
            sync_status="succeeded",
            data_freshness_status="fresh",
            sync_timestamp=now,
            received_at=now,
        ),
    ]

    refresh_snaptrade_connections(db_session, user.id, adapter)

    broker_accounts = db_session.query(BrokerAccount).order_by(BrokerAccount.display_name).all()
    assert len({broker_account.account_id for broker_account in broker_accounts}) == 2
    assert all(broker_account.account_id != shared_account.id for broker_account in broker_accounts)
