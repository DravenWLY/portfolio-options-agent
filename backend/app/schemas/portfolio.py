from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PortfolioWarningRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    severity: str
    message: str
    freshness_status: str
    source: str


class PortfolioSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: UUID
    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cash_as_of: datetime | None
    stock_positions_as_of: datetime | None
    option_positions_as_of: datetime | None
    latest_snapshot_as_of: datetime | None
    total_cash: Decimal
    stock_position_count: int
    stock_market_value: Decimal = Field(
        description="Sum of latest stock/ETF snapshots that supplied market value. "
        "Positions missing market value still count toward stock_position_count and emit broker_data_market_value_missing.",
    )
    option_position_count: int
    long_option_position_count: int
    short_option_position_count: int
    option_market_value: Decimal = Field(
        description="Signed sum of latest option snapshots that supplied market value. "
        "Positions missing market value still count toward option_position_count and emit broker_data_market_value_missing.",
    )
    total_internal_value: Decimal
    data_sources: list[str]
    data_freshness_statuses: list[str]
    broker_data_warnings: list[PortfolioWarningRead]
