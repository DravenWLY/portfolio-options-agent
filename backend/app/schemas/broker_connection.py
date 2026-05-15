from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.broker_sync_status import ConnectionStatus, DataFreshnessStatus, SyncStatus

BrokerProvider = Literal["snaptrade", "akoya", "plaid", "manual", "csv", "other"]


class BrokerConnectionCreate(BaseModel):
    provider: BrokerProvider = "snaptrade"
    broker_name: str = Field(min_length=1, max_length=120)
    provider_connection_id: str = Field(min_length=1, max_length=160)
    connection_status: ConnectionStatus = "unknown"
    sync_status: SyncStatus = "idle"
    data_freshness_status: DataFreshnessStatus = "unknown"
    last_successful_sync_at: datetime | None = None
    last_attempted_sync_at: datetime | None = None
    consent_expires_at: datetime | None = None
    secret_ref: str | None = Field(default=None, max_length=255)
    scopes: list[str] | None = None
    raw_metadata: dict | None = None

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("broker_name", "provider_connection_id")
    @classmethod
    def strip_required_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("secret_ref")
    @classmethod
    def reject_plaintext_secrets(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        lowered = stripped.lower()
        forbidden_fragments = ("password", "token=", "apikey", "api_key", "secret=")
        if any(fragment in lowered for fragment in forbidden_fragments):
            raise ValueError("secret_ref must be a reference, not plaintext credential material")
        return stripped


class BrokerConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    provider: str
    broker_name: str
    provider_connection_id: str
    connection_status: str
    sync_status: str
    data_freshness_status: str
    last_successful_sync_at: datetime | None
    last_attempted_sync_at: datetime | None
    consent_expires_at: datetime | None
    secret_ref: str | None
    scopes: list[str] | None
    raw_metadata: dict | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
