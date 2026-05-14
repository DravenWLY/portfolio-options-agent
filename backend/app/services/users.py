from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(display_name=payload.display_name, email=str(payload.email) if payload.email else None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())))


def get_user(db: Session, user_id: UUID) -> User | None:
    return db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
