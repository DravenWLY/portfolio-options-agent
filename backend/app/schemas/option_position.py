from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.broker_sync_status import DataFreshnessStatus
from app.schemas.option_contract import OptionContractCreate


Quantity = Annotated[Decimal, Field(gt=Decimal("0"), max_digits=20, decimal_places=6)]
PriceAmount = Annotated[Decimal, Field(ge=Decimal("0"), max_digits=18, decimal_places=4)]
MoneyAmount = Annotated[Decimal, Field(ge=Decimal("0"), max_digits=18, decimal_places=2)]

PositionSide = Literal["long", "short"]
OptionPositionStatus = Literal["open", "closed", "assigned", "expired", "called_away"]
PositionSource = Literal["manual", "csv", "snaptrade"]


class OptionPositionCreate(BaseModel):
    contract: OptionContractCreate
    position_side: PositionSide
    quantity: Quantity
    average_price: PriceAmount | None = None
    market_price: PriceAmount | None = None
    market_value: MoneyAmount | None = None
    status: OptionPositionStatus = "open"
    source: PositionSource = "manual"
    source_ref: str | None = Field(default=None, max_length=120)
    data_freshness_status: DataFreshnessStatus = "unknown"
    raw_provider_payload: dict | None = None
    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))
    opened_at: datetime | None = None
    closed_at: datetime | None = None


class OptionPositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    option_contract_id: UUID
    position_side: PositionSide
    quantity: Decimal
    average_price: Decimal | None
    market_price: Decimal | None
    market_value: Decimal | None
    status: OptionPositionStatus
    source: PositionSource
    source_ref: str | None
    data_freshness_status: DataFreshnessStatus
    raw_provider_payload: dict | None
    as_of: datetime
    opened_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
