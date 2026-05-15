from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SnapTradeUserRegistrationRequest(BaseModel):
    user_id: UUID


class SnapTradeUserRegistrationRead(BaseModel):
    provider: Literal["snaptrade"] = "snaptrade"
    snaptrade_user_id: str
    credential_metadata_id: UUID


class SnapTradeConnectionPortalRequest(BaseModel):
    user_id: UUID


class SnapTradeConnectionPortalRead(BaseModel):
    provider: Literal["snaptrade"] = "snaptrade"
    portal_url: str
    expires_at: datetime | None


class BrokerConnectionPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    provider: str
    broker_name: str
    connection_status: str
    sync_status: str
    data_freshness_status: str
    last_successful_sync_at: datetime | None
    last_attempted_sync_at: datetime | None
    consent_expires_at: datetime | None
    scopes: list[str] | None
    created_at: datetime
    updated_at: datetime


class BrokerAccountPublicRead(BaseModel):
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
    created_at: datetime
    updated_at: datetime


class BrokerAccountSyncRequest(BaseModel):
    trigger: Literal["manual", "scheduled", "webhook", "retry", "system"] = "manual"


class BrokerSyncErrorRead(BaseModel):
    type: str
    message: str


class BrokerSyncPartialFailureRead(BaseModel):
    occ_symbol: str | None = None
    reason: str


class BrokerSyncSummaryRead(BaseModel):
    balance_currency: str | None = None
    stock_positions_count: int | None = None
    option_positions_count: int | None = None
    partial_failures: list[BrokerSyncPartialFailureRead] = []
    warnings: list[str] = []
    provider_request_id: str | None = None


class BrokerSyncRunPublicRead(BaseModel):
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
    error: BrokerSyncErrorRead | None
    summary: BrokerSyncSummaryRead | None
    created_at: datetime
    updated_at: datetime


class BrokerProviderErrorRead(BaseModel):
    detail: str = Field(min_length=1)


class BrokerSyncConflictRead(BaseModel):
    sync_run_id: str
    status: str


class BrokerSyncFreshnessRead(BaseModel):
    user_id: UUID
    broker_connection_id: UUID
    broker_account_id: UUID
    account_id: UUID | None
    provider: str
    broker_name: str
    freshness_scope: Literal["broker_portfolio"] = "broker_portfolio"
    connection_status: str
    sync_status: str
    data_freshness_status: str
    last_successful_sync_at: datetime | None
    last_attempted_sync_at: datetime | None
    latest_sync_run_id: UUID | None
    latest_sync_run_status: str | None
    latest_sync_run_completed_at: datetime | None
    requires_reauth: bool
    has_error: bool
