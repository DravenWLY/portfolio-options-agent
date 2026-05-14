from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.cash_balance import CashBalanceCreate, CashBalanceRead
from app.services.portfolio import cash_balances as cash_balance_service

router = APIRouter(prefix="/accounts/{account_id}", tags=["portfolio"])


@router.post("/cash-balances", response_model=CashBalanceRead, status_code=status.HTTP_201_CREATED)
def create_cash_balance(
    account_id: UUID,
    payload: CashBalanceCreate,
    db: Session = Depends(get_db),
) -> CashBalanceRead:
    cash_balance = cash_balance_service.create_cash_balance(db, account_id, payload)
    if cash_balance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return cash_balance


@router.get("/cash-balances/latest", response_model=CashBalanceRead)
def get_latest_cash_balance(account_id: UUID, db: Session = Depends(get_db)) -> CashBalanceRead:
    cash_balance = cash_balance_service.get_latest_cash_balance(db, account_id)
    if cash_balance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash balance not found")
    return cash_balance
