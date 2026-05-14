from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.cash_balance import CashBalance
from app.schemas.cash_balance import CashBalanceCreate


def account_exists(db: Session, account_id: UUID) -> bool:
    return db.scalar(select(Account.id).where(Account.id == account_id, Account.deleted_at.is_(None))) is not None


def create_cash_balance(db: Session, account_id: UUID, payload: CashBalanceCreate) -> CashBalance | None:
    if not account_exists(db, account_id):
        return None

    cash_balance = CashBalance(
        account_id=account_id,
        total_cash=payload.total_cash,
        reserved_collateral_cash=payload.reserved_collateral_cash,
        free_cash=payload.free_cash,
        premium_income_cash=payload.premium_income_cash,
        dca_cash=payload.dca_cash,
        as_of=payload.as_of,
    )
    db.add(cash_balance)
    db.commit()
    db.refresh(cash_balance)
    return cash_balance


def get_latest_cash_balance(db: Session, account_id: UUID) -> CashBalance | None:
    return db.scalar(
        select(CashBalance)
        .join(Account, CashBalance.account_id == Account.id)
        .where(CashBalance.account_id == account_id, Account.deleted_at.is_(None))
        .order_by(CashBalance.as_of.desc(), CashBalance.created_at.desc())
        .limit(1)
    )
