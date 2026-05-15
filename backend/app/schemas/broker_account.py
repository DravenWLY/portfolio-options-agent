from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.broker_sync_status import DataFreshnessStatus, SyncStatus

AccountType = Literal["taxable_individual", "roth_ira", "traditional_ira", "other"]


class BrokerAccountCreate(BaseModel):
    broker_connection_id: UUID
    account_id: UUID | None = None
    provider_account_id: str = Field(min_length=1, max_length=160)
    display_name: str = Field(min_length=1, max_length=120)
    account_type: AccountType = "other"
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    sync_status: SyncStatus = "idle"
    data_freshness_status: DataFreshnessStatus = "unknown"
    last_successful_sync_at: datetime | None = None
    raw_payload: dict | None = None

    @field_validator("provider_account_id", "display_name")
    @classmethod
    def strip_required_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("base_currency")
    @classmethod
    def normalize_base_currency(cls, value: str) -> str:
        return value.strip().upper()


class BrokerAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    broker_connection_id: UUID
    account_id: UUID | None
    provider_account_id: str
    display_name: str
    account_type: str
    base_currency: str
    sync_status: str
    data_freshness_status: str
    last_successful_sync_at: datetime | None
    raw_payload: dict | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
