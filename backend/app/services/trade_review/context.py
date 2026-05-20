from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.cash_balance import CashBalanceRead
from app.schemas.option_position import OptionPositionRead
from app.schemas.portfolio import PortfolioSummaryRead
from app.schemas.stock_position import StockPositionRead


@dataclass(frozen=True)
class CashContext:
    total_cash: Decimal
    free_cash: Decimal
    reserved_collateral_cash: Decimal
    data_freshness_status: str
    as_of: datetime
    source: str


@dataclass(frozen=True)
class StockPositionContext:
    symbol: str
    asset_type: str
    quantity: Decimal
    market_value: Decimal | None
    data_freshness_status: str
    as_of: datetime
    source: str


@dataclass(frozen=True)
class OptionPositionContext:
    option_contract_id: UUID
    position_side: str
    quantity: Decimal
    market_value: Decimal | None
    status: str
    data_freshness_status: str
    as_of: datetime
    source: str


@dataclass(frozen=True)
class PortfolioReviewContext:
    user_id: UUID
    account_id: UUID
    summary_as_of: datetime
    latest_snapshot_as_of: datetime | None
    total_internal_value: Decimal
    data_sources: tuple[str, ...]
    data_freshness_statuses: tuple[str, ...]
    cash: CashContext | None
    stock_positions: tuple[StockPositionContext, ...]
    option_positions: tuple[OptionPositionContext, ...]


class PortfolioContextBuilder:
    """Build sanitized deterministic context from internal portfolio records."""

    def build(
        self,
        *,
        user_id: UUID,
        summary: PortfolioSummaryRead,
        cash_balance: CashBalanceRead | None = None,
        stock_positions: tuple[StockPositionRead, ...] = (),
        option_positions: tuple[OptionPositionRead, ...] = (),
    ) -> PortfolioReviewContext:
        cash_context = None
        if cash_balance is not None:
            cash_context = CashContext(
                total_cash=cash_balance.total_cash,
                free_cash=cash_balance.free_cash,
                reserved_collateral_cash=cash_balance.reserved_collateral_cash,
                data_freshness_status=cash_balance.data_freshness_status,
                as_of=cash_balance.as_of,
                source=str(cash_balance.source),
            )

        return PortfolioReviewContext(
            user_id=user_id,
            account_id=summary.account_id,
            summary_as_of=summary.as_of,
            latest_snapshot_as_of=summary.latest_snapshot_as_of,
            total_internal_value=summary.total_internal_value,
            data_sources=tuple(summary.data_sources),
            data_freshness_statuses=tuple(summary.data_freshness_statuses),
            cash=cash_context,
            stock_positions=tuple(
                StockPositionContext(
                    symbol=position.symbol,
                    asset_type=position.asset_type,
                    quantity=position.quantity,
                    market_value=position.market_value,
                    data_freshness_status=position.data_freshness_status,
                    as_of=position.as_of,
                    source=position.source,
                )
                for position in stock_positions
            ),
            option_positions=tuple(
                OptionPositionContext(
                    option_contract_id=position.option_contract_id,
                    position_side=position.position_side,
                    quantity=position.quantity,
                    market_value=position.market_value,
                    status=position.status,
                    data_freshness_status=position.data_freshness_status,
                    as_of=position.as_of,
                    source=position.source,
                )
                for position in option_positions
            ),
        )
