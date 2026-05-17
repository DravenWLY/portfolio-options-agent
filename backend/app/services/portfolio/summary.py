from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.cash_balance import CashBalance
from app.models.option_position import OptionPosition
from app.models.stock_position import StockPosition
from app.schemas.portfolio import PortfolioSummaryRead
from app.services.portfolio.warnings import generate_broker_data_warnings, generate_missing_market_value_warning


ZERO = Decimal("0")
CASH_EQUIVALENT_STOCK_SYMBOLS = {
    # Fidelity sweep / money-market core positions. These also appear in cash
    # balances, so including them in stock book value double-counts cash.
    "SPAXX",
    "FDRXX",
    "FZFXX",
    "FCASH",
}


class _PositionSnapshot(Protocol):
    as_of: datetime


def _money_or_zero(value: Decimal | None) -> Decimal:
    return value if value is not None else ZERO


def _unique_sorted(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def _signed_option_market_value(position: OptionPosition) -> Decimal:
    market_value = _money_or_zero(position.market_value)
    if position.position_side == "short":
        return -market_value
    return market_value


def _latest_as_of(positions: list[_PositionSnapshot]) -> datetime | None:
    if not positions:
        return None
    return max(position.as_of for position in positions)


def _latest_available_as_of(*values: datetime | None) -> datetime | None:
    populated_values = [value for value in values if value is not None]
    if not populated_values:
        return None
    return max(populated_values)


def _has_missing_market_value(positions: list[StockPosition] | list[OptionPosition]) -> bool:
    return any(position.market_value is None for position in positions)


def _is_stock_summary_position(position: StockPosition) -> bool:
    """Exclude legacy provider rows that were misclassified before option ingestion existed."""
    descriptor = f"{position.asset_type or ''} {position.symbol or ''}".lower()
    return "option" not in descriptor and " call" not in descriptor and " put" not in descriptor


def _is_cash_equivalent_stock_position(position: StockPosition) -> bool:
    return (position.symbol or "").upper() in CASH_EQUIVALENT_STOCK_SYMBOLS


def get_portfolio_summary(db: Session, account_id: UUID) -> PortfolioSummaryRead | None:
    account_exists = db.scalar(select(Account.id).where(Account.id == account_id, Account.deleted_at.is_(None)))
    if account_exists is None:
        return None

    latest_cash = db.scalar(
        select(CashBalance)
        .where(CashBalance.account_id == account_id)
        .order_by(CashBalance.as_of.desc(), CashBalance.created_at.desc())
        .limit(1)
    )
    stock_rows = db.scalars(
        select(StockPosition)
        .where(StockPosition.account_id == account_id)
        .order_by(
            StockPosition.symbol.asc(),
            StockPosition.as_of.desc(),
            StockPosition.created_at.desc(),
            StockPosition.id.desc(),
        )
    )
    latest_stock_positions = {}
    for position in stock_rows:
        if not _is_stock_summary_position(position):
            continue
        if _is_cash_equivalent_stock_position(position):
            continue
        latest_stock_positions.setdefault(position.symbol, position)

    option_rows = db.scalars(
        select(OptionPosition)
        .where(OptionPosition.account_id == account_id, OptionPosition.status == "open")
        .order_by(
            OptionPosition.option_contract_id.asc(),
            OptionPosition.as_of.desc(),
            OptionPosition.created_at.desc(),
            OptionPosition.id.desc(),
        )
    )
    latest_option_positions = {}
    for position in option_rows:
        latest_option_positions.setdefault(position.option_contract_id, position)

    stock_positions = list(latest_stock_positions.values())
    option_positions = list(latest_option_positions.values())

    total_cash = _money_or_zero(latest_cash.total_cash if latest_cash else None)
    stock_market_value = sum((_money_or_zero(position.market_value) for position in stock_positions), ZERO)
    option_market_value = sum((_signed_option_market_value(position) for position in option_positions), ZERO)
    long_option_count = sum(1 for position in option_positions if position.position_side == "long")
    short_option_count = sum(1 for position in option_positions if position.position_side == "short")
    stock_positions_as_of = _latest_as_of(stock_positions)
    option_positions_as_of = _latest_as_of(option_positions)

    data_sources = []
    freshness_statuses = []
    if latest_cash is not None:
        data_sources.append(latest_cash.source)
        freshness_statuses.append(latest_cash.data_freshness_status)
    data_sources.extend(position.source for position in stock_positions)
    data_sources.extend(position.source for position in option_positions)
    freshness_statuses.extend(position.data_freshness_status for position in stock_positions)
    freshness_statuses.extend(position.data_freshness_status for position in option_positions)

    data_freshness_statuses = _unique_sorted(freshness_statuses)
    broker_data_warnings = generate_broker_data_warnings(data_freshness_statuses)
    if _has_missing_market_value(stock_positions) or _has_missing_market_value(option_positions):
        broker_data_warnings.append(generate_missing_market_value_warning())

    return PortfolioSummaryRead(
        account_id=account_id,
        as_of=datetime.now(UTC),
        cash_as_of=latest_cash.as_of if latest_cash else None,
        stock_positions_as_of=stock_positions_as_of,
        option_positions_as_of=option_positions_as_of,
        latest_snapshot_as_of=_latest_available_as_of(
            latest_cash.as_of if latest_cash else None,
            stock_positions_as_of,
            option_positions_as_of,
        ),
        total_cash=total_cash,
        stock_position_count=len(stock_positions),
        stock_market_value=stock_market_value,
        option_position_count=len(option_positions),
        long_option_position_count=long_option_count,
        short_option_position_count=short_option_count,
        option_market_value=option_market_value,
        total_internal_value=total_cash + stock_market_value + option_market_value,
        data_sources=_unique_sorted(data_sources),
        data_freshness_statuses=data_freshness_statuses,
        broker_data_warnings=broker_data_warnings,
    )
