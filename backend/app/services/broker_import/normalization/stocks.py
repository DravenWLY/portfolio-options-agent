from uuid import UUID

from sqlalchemy.orm import Session

from app.models.stock_position import StockPosition
from app.services.broker_import import reconciliation
from app.services.broker_import.normalization.sanitization import sanitize_provider_payload
from app.services.broker_import.providers.models import ProviderPositionSnapshot


def normalize_stock_position(
    db: Session,
    account_id: UUID,
    position: ProviderPositionSnapshot,
) -> StockPosition:
    symbol = position.symbol.strip().upper()
    ref = reconciliation.source_ref(position.provider_account_id, symbol)
    existing = reconciliation.find_stock_snapshot(
        db,
        account_id,
        symbol,
        position.provider,
        ref,
        position.sync_timestamp,
    )

    if existing is None:
        existing = StockPosition(
            account_id=account_id,
            symbol=symbol,
            source=position.provider,
            source_ref=ref,
            as_of=position.sync_timestamp,
        )
        db.add(existing)

    existing.asset_type = position.asset_type
    existing.quantity = position.quantity
    existing.cost_basis = None
    existing.market_price = None
    existing.market_value = position.market_value
    existing.data_freshness_status = position.data_freshness_status
    existing.raw_provider_payload = sanitize_provider_payload(position.raw_payload)
    db.flush()
    return existing


def normalize_stock_positions(
    db: Session,
    account_id: UUID,
    positions: list[ProviderPositionSnapshot],
) -> list[StockPosition]:
    return [normalize_stock_position(db, account_id, position) for position in positions]
