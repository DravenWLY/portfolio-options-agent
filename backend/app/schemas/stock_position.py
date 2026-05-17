from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.broker_sync_status import DataFreshnessStatus


Quantity = Annotated[Decimal, Field(gt=Decimal("0"), max_digits=20, decimal_places=6)]
MoneyAmount = Annotated[Decimal, Field(ge=Decimal("0"), max_digits=18, decimal_places=2)]
PriceAmount = Annotated[Decimal, Field(ge=Decimal("0"), max_digits=18, decimal_places=4)]

AssetType = Literal["stock", "etf", "mutual_fund", "cash_equivalent", "other"]
PositionSource = Literal["manual", "csv", "snaptrade"]


class StockPositionCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=24)
    asset_type: AssetType = "stock"
    quantity: Quantity
    cost_basis: MoneyAmount | None = None
    market_price: PriceAmount | None = None
    market_value: MoneyAmount | None = None
    source: PositionSource = "manual"
    source_ref: str | None = Field(default=None, max_length=120)
    data_freshness_status: DataFreshnessStatus = "unknown"
    raw_provider_payload: dict | None = None
    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class StockPositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    symbol: str
    asset_type: str
    quantity: Decimal
    cost_basis: Decimal | None
    market_price: Decimal | None
    market_value: Decimal | None
    source: PositionSource
    source_ref: str | None
    data_freshness_status: DataFreshnessStatus
    raw_provider_payload: dict | None
    as_of: datetime
    created_at: datetime
    updated_at: datetime
