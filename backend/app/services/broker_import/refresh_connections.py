from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun
from app.services import accounts as account_service
from app.services.broker_import.normalization.sanitization import (
    BROKER_ACCOUNT_PAYLOAD_ALLOWLIST,
    BROKER_CONNECTION_METADATA_ALLOWLIST,
    allowlisted_provider_payload,
    sanitized_sync_summary,
)
from app.services.broker_import.providers.snaptrade import SnapTradeAdapter


class BrokerConnectionRefreshUserNotFoundError(RuntimeError):
    """Raised when connection refresh is requested for a missing user."""


def _raw_provider_request_id(payload: dict | None) -> str | None:
    if not payload:
        return None
    value = payload.get("provider_request_id") or payload.get("request_id")
    return str(value) if value else None


def refresh_snaptrade_connections(
    db: Session,
    user_id: UUID,
    adapter: SnapTradeAdapter,
) -> BrokerSyncRun:
    if not account_service.user_exists(db, user_id):
        raise BrokerConnectionRefreshUserNotFoundError("User not found")

    connection_snapshots = adapter.list_connections(str(user_id))
    account_snapshots_by_connection = {
        snapshot.provider_connection_id: adapter.list_accounts(snapshot.provider_connection_id)
        for snapshot in connection_snapshots
    }

    started_at = datetime.now(UTC)
    sync_run = BrokerSyncRun(
        broker_connection_id=None,
        trigger="manual",
        status="running",
        started_at=started_at,
    )
    warnings: list[str] = []
    provider_request_ids: list[str] = []

    first_connection_id: UUID | None = None
    accounts_count = 0
    for connection_snapshot in connection_snapshots:
        connection = db.scalar(
            select(BrokerConnection).where(
                BrokerConnection.provider == connection_snapshot.provider,
                BrokerConnection.provider_connection_id == connection_snapshot.provider_connection_id,
                BrokerConnection.deleted_at.is_(None),
            )
        )
        if connection is None:
            connection = BrokerConnection(
                user_id=user_id,
                provider=connection_snapshot.provider,
                broker_name=connection_snapshot.broker_name,
                provider_connection_id=connection_snapshot.provider_connection_id,
            )
            db.add(connection)
            db.flush()

        connection.user_id = user_id
        connection.broker_name = connection_snapshot.broker_name
        connection.connection_status = connection_snapshot.connection_status
        connection.sync_status = connection_snapshot.sync_status
        connection.data_freshness_status = connection_snapshot.data_freshness_status
        connection.last_attempted_sync_at = started_at
        if connection_snapshot.sync_status in {"succeeded", "partially_succeeded"}:
            connection.last_successful_sync_at = connection_snapshot.sync_timestamp or started_at
        connection.raw_metadata = allowlisted_provider_payload(
            connection_snapshot.raw_payload,
            BROKER_CONNECTION_METADATA_ALLOWLIST,
        )
        warnings.extend(connection_snapshot.warnings)
        provider_request_id = _raw_provider_request_id(connection_snapshot.raw_payload)
        if provider_request_id:
            provider_request_ids.append(provider_request_id)
        if first_connection_id is None:
            first_connection_id = connection.id

        for account_snapshot in account_snapshots_by_connection[connection_snapshot.provider_connection_id]:
            internal_account = account_service.find_or_create_synced_account(
                db,
                user_id=user_id,
                broker_name=connection_snapshot.broker_name,
                account_type=account_snapshot.account_type,
                display_name=account_snapshot.display_name,
                base_currency=account_snapshot.base_currency,
            )
            broker_account = db.scalar(
                select(BrokerAccount).where(
                    BrokerAccount.broker_connection_id == connection.id,
                    BrokerAccount.provider_account_id == account_snapshot.provider_account_id,
                    BrokerAccount.deleted_at.is_(None),
                )
            )
            if broker_account is None:
                broker_account = BrokerAccount(
                    broker_connection_id=connection.id,
                    provider_account_id=account_snapshot.provider_account_id,
                )
                db.add(broker_account)

            broker_account.account_id = internal_account.id
            broker_account.display_name = account_snapshot.display_name
            broker_account.account_type = account_snapshot.account_type
            broker_account.base_currency = account_snapshot.base_currency
            broker_account.sync_status = account_snapshot.sync_status
            broker_account.data_freshness_status = account_snapshot.data_freshness_status
            if account_snapshot.sync_status in {"succeeded", "partially_succeeded"}:
                broker_account.last_successful_sync_at = account_snapshot.sync_timestamp or started_at
            broker_account.raw_payload = allowlisted_provider_payload(
                account_snapshot.raw_payload,
                BROKER_ACCOUNT_PAYLOAD_ALLOWLIST,
            )
            accounts_count += 1

    if first_connection_id is None:
        raise BrokerConnectionRefreshUserNotFoundError("No SnapTrade connections found")

    sync_run.broker_connection_id = first_connection_id
    sync_run.status = "succeeded"
    sync_run.completed_at = datetime.now(UTC)
    sync_run.provider_request_id = provider_request_ids[0] if provider_request_ids else None
    sync_run.accounts_count = accounts_count
    sync_run.summary = sanitized_sync_summary(
        warnings=warnings,
        provider_request_id=sync_run.provider_request_id,
    )
    db.add(sync_run)
    db.commit()
    db.refresh(sync_run)
    return sync_run
