from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.stock_position import StockPosition
from app.schemas.stock_position import StockPositionCreate


def account_exists(db: Session, account_id: UUID) -> bool:
    return db.scalar(select(Account.id).where(Account.id == account_id, Account.deleted_at.is_(None))) is not None


def create_stock_position(db: Session, account_id: UUID, payload: StockPositionCreate) -> StockPosition | None:
    if not account_exists(db, account_id):
        return None

    stock_position = StockPosition(
        account_id=account_id,
        symbol=payload.symbol,
        asset_type=payload.asset_type,
        quantity=payload.quantity,
        cost_basis=payload.cost_basis,
        market_price=payload.market_price,
        market_value=payload.market_value,
        source=payload.source,
        source_ref=payload.source_ref,
        data_freshness_status=payload.data_freshness_status,
        raw_provider_payload=payload.raw_provider_payload,
        as_of=payload.as_of,
    )
    db.add(stock_position)
    db.commit()
    db.refresh(stock_position)
    return stock_position


def list_stock_positions(db: Session, account_id: UUID) -> list[StockPosition] | None:
    if not account_exists(db, account_id):
        return None

    return list(
        db.scalars(
            select(StockPosition)
            .where(StockPosition.account_id == account_id)
            .order_by(StockPosition.symbol.asc(), StockPosition.as_of.desc())
        )
    )
