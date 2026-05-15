from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun


def get_broker_sync_run(db: Session, sync_run_id: UUID) -> BrokerSyncRun | None:
    return db.scalar(select(BrokerSyncRun).where(BrokerSyncRun.id == sync_run_id))


def get_user_broker_sync_run(db: Session, user_id: UUID, sync_run_id: UUID) -> BrokerSyncRun | None:
    return db.scalar(
        select(BrokerSyncRun)
        .join(BrokerConnection, BrokerSyncRun.broker_connection_id == BrokerConnection.id)
        .where(
            BrokerSyncRun.id == sync_run_id,
            BrokerConnection.user_id == user_id,
            BrokerConnection.deleted_at.is_(None),
        )
    )


def get_active_sync_run(db: Session, broker_account_id: UUID) -> BrokerSyncRun | None:
    return db.scalar(
        select(BrokerSyncRun)
        .join(BrokerAccount, BrokerSyncRun.broker_account_id == BrokerAccount.id)
        .where(
            BrokerSyncRun.broker_account_id == broker_account_id,
            BrokerSyncRun.status.in_(("queued", "running")),
        )
        .order_by(BrokerSyncRun.created_at.desc())
        .limit(1)
    )
