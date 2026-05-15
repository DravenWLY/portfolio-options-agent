from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


StrikeAmount = Annotated[Decimal, Field(gt=Decimal("0"), max_digits=18, decimal_places=4)]
MultiplierAmount = Annotated[Decimal, Field(gt=Decimal("0"), max_digits=10, decimal_places=2)]
OptionType = Literal["call", "put"]
OptionStyle = Literal["american", "european", "unknown"]


class OptionContractCreate(BaseModel):
    occ_symbol: str = Field(min_length=1, max_length=64)
    underlying_symbol: str = Field(min_length=1, max_length=24)
    expiration_date: date
    strike: StrikeAmount
    option_type: OptionType
    style: OptionStyle = "american"
    multiplier: MultiplierAmount = Decimal("100")

    @field_validator("occ_symbol", "underlying_symbol")
    @classmethod
    def normalize_symbols(cls, value: str) -> str:
        return value.strip().upper()


class OptionContractRead(OptionContractCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
