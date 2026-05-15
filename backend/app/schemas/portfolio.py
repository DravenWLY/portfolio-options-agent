from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PortfolioSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: UUID
    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cash_as_of: datetime | None
    total_cash: Decimal
    stock_position_count: int
    stock_market_value: Decimal
    option_position_count: int
    long_option_position_count: int
    short_option_position_count: int
    option_market_value: Decimal
    total_internal_value: Decimal
    data_sources: list[str]
    data_freshness_statuses: list[str]
