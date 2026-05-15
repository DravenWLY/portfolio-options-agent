from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.cash_balance import CashBalanceCreate, CashBalanceRead
from app.schemas.option_position import OptionPositionCreate, OptionPositionRead
from app.schemas.portfolio import PortfolioSummaryRead
from app.schemas.stock_position import StockPositionCreate, StockPositionRead
from app.services.portfolio import cash_balances as cash_balance_service
from app.services.portfolio import option_positions as option_position_service
from app.services.portfolio import summary as summary_service
from app.services.portfolio import stock_positions as stock_position_service

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


@router.post("/stock-positions", response_model=StockPositionRead, status_code=status.HTTP_201_CREATED)
def create_stock_position(
    account_id: UUID,
    payload: StockPositionCreate,
    db: Session = Depends(get_db),
) -> StockPositionRead:
    stock_position = stock_position_service.create_stock_position(db, account_id, payload)
    if stock_position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return stock_position


@router.get("/stock-positions", response_model=list[StockPositionRead])
def list_stock_positions(account_id: UUID, db: Session = Depends(get_db)) -> list[StockPositionRead]:
    stock_positions = stock_position_service.list_stock_positions(db, account_id)
    if stock_positions is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return stock_positions


@router.post("/option-positions", response_model=OptionPositionRead, status_code=status.HTTP_201_CREATED)
def create_option_position(
    account_id: UUID,
    payload: OptionPositionCreate,
    db: Session = Depends(get_db),
) -> OptionPositionRead:
    option_position = option_position_service.create_option_position(db, account_id, payload)
    if option_position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return option_position


@router.get("/option-positions", response_model=list[OptionPositionRead])
def list_option_positions(account_id: UUID, db: Session = Depends(get_db)) -> list[OptionPositionRead]:
    option_positions = option_position_service.list_option_positions(db, account_id)
    if option_positions is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return option_positions


@router.get("/portfolio", response_model=PortfolioSummaryRead)
def get_portfolio_summary(account_id: UUID, db: Session = Depends(get_db)) -> PortfolioSummaryRead:
    summary = summary_service.get_portfolio_summary(db, account_id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return summary
