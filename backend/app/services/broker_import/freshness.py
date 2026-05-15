from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun
from app.schemas.broker_sync_api import BrokerSyncFreshnessRead


ERROR_STATUSES = {"error", "failed"}
ERROR_SYNC_RUN_STATUSES = {"failed", "partially_succeeded"}
REAUTH_STATUSES = {"reauth_required"}


def _latest_broker_account_sync_run(db: Session, broker_account_id: UUID) -> BrokerSyncRun | None:
    return db.scalar(
        select(BrokerSyncRun)
        .where(BrokerSyncRun.broker_account_id == broker_account_id)
        .order_by(BrokerSyncRun.created_at.desc(), BrokerSyncRun.id.desc())
        .limit(1)
    )


def get_broker_account_freshness(
    db: Session,
    user_id: UUID,
    broker_account_id: UUID,
) -> BrokerSyncFreshnessRead | None:
    row = db.execute(
        select(BrokerAccount, BrokerConnection)
        .join(BrokerConnection, BrokerAccount.broker_connection_id == BrokerConnection.id)
        .where(
            BrokerAccount.id == broker_account_id,
            BrokerAccount.deleted_at.is_(None),
            BrokerConnection.user_id == user_id,
            BrokerConnection.deleted_at.is_(None),
        )
    ).first()
    if row is None:
        return None

    broker_account, broker_connection = row
    latest_run = _latest_broker_account_sync_run(db, broker_account.id)
    statuses = {
        broker_connection.connection_status,
        broker_connection.sync_status,
        broker_connection.data_freshness_status,
        broker_account.sync_status,
        broker_account.data_freshness_status,
    }
    if latest_run is not None:
        statuses.add(latest_run.status)

    return BrokerSyncFreshnessRead(
        user_id=user_id,
        broker_connection_id=broker_connection.id,
        broker_account_id=broker_account.id,
        account_id=broker_account.account_id,
        provider=broker_connection.provider,
        broker_name=broker_connection.broker_name,
        connection_status=broker_connection.connection_status,
        sync_status=broker_account.sync_status,
        data_freshness_status=broker_account.data_freshness_status,
        last_successful_sync_at=broker_account.last_successful_sync_at,
        last_attempted_sync_at=broker_connection.last_attempted_sync_at,
        latest_sync_run_id=latest_run.id if latest_run else None,
        latest_sync_run_status=latest_run.status if latest_run else None,
        latest_sync_run_completed_at=latest_run.completed_at if latest_run else None,
        requires_reauth=bool(statuses & REAUTH_STATUSES),
        has_error=bool(statuses & ERROR_STATUSES)
        or (latest_run is not None and latest_run.status == "partially_succeeded"),
    )
