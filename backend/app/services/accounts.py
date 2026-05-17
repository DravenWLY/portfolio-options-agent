from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import exists, or_, select
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

    from app.models.broker_account import BrokerAccount

    linked_broker_account = exists().where(
        BrokerAccount.account_id == Account.id,
        BrokerAccount.deleted_at.is_(None),
    )
    return list(
        db.scalars(
            select(Account)
            .where(
                Account.user_id == user_id,
                Account.deleted_at.is_(None),
                or_(Account.is_manual.is_(True), linked_broker_account),
            )
            .order_by(Account.created_at.desc())
        )
    )


def get_account(db: Session, account_id: UUID) -> Account | None:
    return db.scalar(select(Account).where(Account.id == account_id, Account.deleted_at.is_(None)))


def find_or_create_synced_account(
    db: Session,
    user_id: UUID,
    broker_name: str,
    account_type: str,
    display_name: str,
    base_currency: str,
) -> Account:
    from app.models.broker_account import BrokerAccount

    candidates = list(
        db.scalars(
            select(Account)
            .where(
                Account.user_id == user_id,
                Account.broker_name == broker_name,
                Account.account_type == account_type,
                Account.display_name == display_name,
                Account.is_manual.is_(True),
                Account.deleted_at.is_(None),
            )
            .order_by(Account.created_at.asc())
        )
    )
    for account in candidates:
        linked = db.scalar(
            select(BrokerAccount.id).where(
                BrokerAccount.account_id == account.id,
                BrokerAccount.deleted_at.is_(None),
            )
        )
        if linked is None:
            account.is_manual = False
            return account

    account = Account(
        user_id=user_id,
        broker_name=broker_name,
        account_type=account_type,
        display_name=display_name,
        base_currency=base_currency,
        is_manual=False,
    )
    db.add(account)
    db.flush()
    return account


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
