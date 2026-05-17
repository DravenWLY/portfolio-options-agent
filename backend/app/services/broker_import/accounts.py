from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.services.broker_import.connections import get_broker_connection


def list_connection_broker_accounts(db: Session, broker_connection_id: UUID) -> list[BrokerAccount] | None:
    if get_broker_connection(db, broker_connection_id) is None:
        return None

    return list(
        db.scalars(
            select(BrokerAccount)
            .where(BrokerAccount.broker_connection_id == broker_connection_id, BrokerAccount.deleted_at.is_(None))
            .order_by(
                BrokerAccount.display_name.asc(),
                BrokerAccount.account_type.asc(),
                BrokerAccount.id.asc(),
            )
        )
    )


def get_broker_account(db: Session, broker_account_id: UUID) -> BrokerAccount | None:
    return db.scalar(
        select(BrokerAccount).where(
            BrokerAccount.id == broker_account_id,
            BrokerAccount.deleted_at.is_(None),
        )
    )


def list_user_connection_broker_accounts(
    db: Session,
    user_id: UUID,
    broker_connection_id: UUID,
) -> list[BrokerAccount] | None:
    connection = db.scalar(
        select(BrokerConnection).where(
            BrokerConnection.id == broker_connection_id,
            BrokerConnection.user_id == user_id,
            BrokerConnection.deleted_at.is_(None),
        )
    )
    if connection is None:
        return None
    return list_connection_broker_accounts(db, broker_connection_id)


def get_user_broker_account(db: Session, user_id: UUID, broker_account_id: UUID) -> BrokerAccount | None:
    return db.scalar(
        select(BrokerAccount)
        .join(BrokerConnection, BrokerAccount.broker_connection_id == BrokerConnection.id)
        .where(
            BrokerAccount.id == broker_account_id,
            BrokerAccount.deleted_at.is_(None),
            BrokerConnection.user_id == user_id,
            BrokerConnection.deleted_at.is_(None),
        )
    )
