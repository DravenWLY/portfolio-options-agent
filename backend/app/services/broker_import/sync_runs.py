from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker_sync_run import BrokerSyncRun


def get_broker_sync_run(db: Session, sync_run_id: UUID) -> BrokerSyncRun | None:
    return db.scalar(select(BrokerSyncRun).where(BrokerSyncRun.id == sync_run_id))
