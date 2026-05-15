from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.models.user import User


def user_exists(db: Session, user_id: UUID) -> bool:
    return db.scalar(select(User.id).where(User.id == user_id, User.deleted_at.is_(None))) is not None


def list_user_broker_connections(db: Session, user_id: UUID) -> list[BrokerConnection] | None:
    if not user_exists(db, user_id):
        return None

    return list(
        db.scalars(
            select(BrokerConnection)
            .where(BrokerConnection.user_id == user_id, BrokerConnection.deleted_at.is_(None))
            .order_by(BrokerConnection.created_at.desc())
        )
    )


def get_broker_connection(db: Session, broker_connection_id: UUID) -> BrokerConnection | None:
    return db.scalar(
        select(BrokerConnection).where(
            BrokerConnection.id == broker_connection_id,
            BrokerConnection.deleted_at.is_(None),
        )
    )


def get_user_broker_connection(db: Session, user_id: UUID, broker_connection_id: UUID) -> BrokerConnection | None:
    return db.scalar(
        select(BrokerConnection).where(
            BrokerConnection.id == broker_connection_id,
            BrokerConnection.user_id == user_id,
            BrokerConnection.deleted_at.is_(None),
        )
    )
