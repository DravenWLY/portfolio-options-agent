from typing import Literal, TypeAlias

from pydantic import BaseModel

from app.services.broker_import.statuses import (
    CONNECTION_STATUSES,
    DATA_FRESHNESS_STATUSES,
    SYNC_RUN_STATUSES,
    SYNC_STATUSES,
    TERMINAL_SYNC_STATUSES,
)

ConnectionStatus: TypeAlias = Literal["connected", "disconnected", "reauth_required", "error", "unknown"]
SyncStatus: TypeAlias = Literal["idle", "queued", "running", "succeeded", "failed", "partially_succeeded", "cancelled"]
SyncRunStatus: TypeAlias = Literal["queued", "running", "succeeded", "failed", "partially_succeeded", "cancelled"]
DataFreshnessStatus: TypeAlias = Literal["fresh", "cached", "delayed", "stale", "unknown", "error", "reauth_required"]


class BrokerSyncStatusCatalog(BaseModel):
    connection_statuses: tuple[str, ...] = CONNECTION_STATUSES
    sync_statuses: tuple[str, ...] = SYNC_STATUSES
    sync_run_statuses: tuple[str, ...] = SYNC_RUN_STATUSES
    data_freshness_statuses: tuple[str, ...] = DATA_FRESHNESS_STATUSES
    terminal_sync_statuses: tuple[str, ...] = TERMINAL_SYNC_STATUSES


def get_broker_sync_status_catalog() -> BrokerSyncStatusCatalog:
    return BrokerSyncStatusCatalog()
