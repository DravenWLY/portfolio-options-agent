from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

AccountType = Literal["taxable_individual", "roth_ira", "traditional_ira", "other"]


class AccountCreate(BaseModel):
    broker_name: str = Field(min_length=1, max_length=80)
    account_type: AccountType
    display_name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)

    @field_validator("base_currency")
    @classmethod
    def normalize_base_currency(cls, value: str) -> str:
        return value.upper()


class AccountUpdate(BaseModel):
    broker_name: str | None = Field(default=None, min_length=1, max_length=80)
    account_type: AccountType | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)

    @field_validator("base_currency")
    @classmethod
    def normalize_base_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    broker_name: str
    account_type: str
    display_name: str
    base_currency: str
    is_manual: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
