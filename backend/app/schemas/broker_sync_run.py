from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.broker_sync_status import SyncRunStatus

SyncTrigger = Literal["manual", "scheduled", "webhook", "retry", "system"]


class BrokerSyncRunCreate(BaseModel):
    broker_connection_id: UUID
    broker_account_id: UUID | None = None
    trigger: SyncTrigger = "manual"
    status: SyncRunStatus = "queued"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    provider_request_id: str | None = Field(default=None, max_length=160)
    accounts_count: int = Field(default=0, ge=0)
    positions_count: int = Field(default=0, ge=0)
    transactions_count: int = Field(default=0, ge=0)
    error: dict | None = None
    summary: dict | None = None

    @field_validator("provider_request_id")
    @classmethod
    def strip_provider_request_id(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def validate_completion_order(self) -> "BrokerSyncRunCreate":
        if self.started_at is not None and self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must be after started_at")
        return self


class BrokerSyncRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    broker_connection_id: UUID
    broker_account_id: UUID | None
    trigger: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    provider_request_id: str | None
    accounts_count: int
    positions_count: int
    transactions_count: int
    error: dict | None
    summary: dict | None
    created_at: datetime
    updated_at: datetime
