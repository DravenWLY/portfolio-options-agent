from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate, AccountUpdate


def user_exists(db: Session, user_id: UUID) -> bool:
    return db.scalar(select(User.id).where(User.id == user_id, User.deleted_at.is_(None))) is not None


def create_account(db: Session, user_id: UUID, payload: AccountCreate) -> Account | None:
    if not user_exists(db, user_id):
        return None

    account = Account(
        user_id=user_id,
        broker_name=payload.broker_name,
        account_type=payload.account_type,
        display_name=payload.display_name,
        base_currency=payload.base_currency,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_user_accounts(db: Session, user_id: UUID) -> list[Account] | None:
    if not user_exists(db, user_id):
        return None

    return list(
        db.scalars(
            select(Account)
            .where(Account.user_id == user_id, Account.deleted_at.is_(None))
            .order_by(Account.created_at.desc())
        )
    )


def get_account(db: Session, account_id: UUID) -> Account | None:
    return db.scalar(select(Account).where(Account.id == account_id, Account.deleted_at.is_(None)))


def update_account(db: Session, account_id: UUID, payload: AccountUpdate) -> Account | None:
    account = get_account(db, account_id)
    if account is None:
        return None

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


def soft_delete_account(db: Session, account_id: UUID) -> bool:
    account = get_account(db, account_id)
    if account is None:
        return False

    account.deleted_at = datetime.now(UTC)
    db.commit()
    return True
