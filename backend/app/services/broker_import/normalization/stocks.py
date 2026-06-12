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
    sync_run_id: UUID | None = None,
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

    existing.instrument_name = _safe_instrument_name(position.instrument_name)
    existing.asset_type = position.asset_type
    existing.sync_run_id = sync_run_id
    existing.quantity = position.quantity
    existing.average_price = position.average_purchase_price
    existing.cost_basis = _stock_cost_basis(position.quantity, position.average_purchase_price)
    existing.market_price = position.market_price
    existing.market_value = position.market_value
    existing.open_pnl = position.open_pnl
    existing.currency = position.currency.strip().upper()
    existing.tax_lots = _serialized_tax_lots(position.tax_lots)
    existing.data_freshness_status = position.data_freshness_status
    existing.raw_provider_payload = sanitize_provider_payload(position.raw_payload)
    db.flush()
    return existing


def _stock_cost_basis(quantity, average_purchase_price):
    if quantity is None or average_purchase_price is None:
        return None
    return abs(quantity) * average_purchase_price


def _safe_instrument_name(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).strip().split())
    return normalized[:160] if normalized else None


def _serialized_tax_lots(tax_lots) -> list[dict] | None:
    serialized = []
    for lot in tax_lots:
        serialized.append(
            {
                "acquired_date": lot.acquired_date.isoformat() if lot.acquired_date else None,
                "quantity": str(lot.quantity) if lot.quantity is not None else None,
                "purchase_price": str(lot.purchase_price) if lot.purchase_price is not None else None,
                "cost_basis": str(lot.cost_basis) if lot.cost_basis is not None else None,
                "current_value": str(lot.current_value) if lot.current_value is not None else None,
                "position_type": lot.position_type,
            }
        )
    return serialized or None


def normalize_stock_positions(
    db: Session,
    account_id: UUID,
    positions: list[ProviderPositionSnapshot],
    sync_run_id: UUID | None = None,
) -> list[StockPosition]:
    return [normalize_stock_position(db, account_id, position, sync_run_id=sync_run_id) for position in positions]
