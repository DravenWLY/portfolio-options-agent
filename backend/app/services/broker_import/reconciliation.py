from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cash_balance import CashBalance
from app.models.option_position import OptionPosition
from app.models.stock_position import StockPosition


def source_ref(provider_account_id: str, identifier: str | None = None) -> str:
    if identifier is None:
        return provider_account_id[:120]
    return f"{provider_account_id}:{identifier}"[:120]


def find_cash_snapshot(
    db: Session,
    account_id: UUID,
    source: str,
    ref: str,
    as_of: datetime,
) -> CashBalance | None:
    return db.scalar(
        select(CashBalance).where(
            CashBalance.account_id == account_id,
            CashBalance.source == source,
            CashBalance.source_ref == ref,
            CashBalance.as_of == as_of,
        )
    )


def find_stock_snapshot(
    db: Session,
    account_id: UUID,
    symbol: str,
    source: str,
    ref: str,
    as_of: datetime,
) -> StockPosition | None:
    return db.scalar(
        select(StockPosition).where(
            StockPosition.account_id == account_id,
            StockPosition.symbol == symbol,
            StockPosition.source == source,
            StockPosition.source_ref == ref,
            StockPosition.as_of == as_of,
        )
    )


def find_option_snapshot(
    db: Session,
    account_id: UUID,
    option_contract_id: UUID,
    source: str,
    ref: str,
    as_of: datetime,
) -> OptionPosition | None:
    return db.scalar(
        select(OptionPosition).where(
            OptionPosition.account_id == account_id,
            OptionPosition.option_contract_id == option_contract_id,
            OptionPosition.source == source,
            OptionPosition.source_ref == ref,
            OptionPosition.as_of == as_of,
        )
    )
