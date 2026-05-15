from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


MoneyAmount = Annotated[Decimal, Field(ge=Decimal("0"), max_digits=18, decimal_places=2)]
CashBalanceSource = Annotated[str, Field(pattern=r"^(manual|csv|snaptrade)$")]
DataFreshnessStatus = Annotated[str, Field(pattern=r"^(fresh|cached|stale|unknown|error|reauth_required)$")]


class CashBalanceCreate(BaseModel):
    total_cash: MoneyAmount
    reserved_collateral_cash: MoneyAmount = Decimal("0.00")
    free_cash: MoneyAmount
    premium_income_cash: MoneyAmount = Decimal("0.00")
    dca_cash: MoneyAmount = Decimal("0.00")
    source: CashBalanceSource = "manual"
    source_ref: str | None = Field(default=None, max_length=120)
    data_freshness_status: DataFreshnessStatus = "unknown"
    as_of: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CashBalanceRead(CashBalanceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    created_at: datetime
