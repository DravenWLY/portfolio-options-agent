from typing import Protocol, runtime_checkable
from uuid import UUID

from app.services.broker_import.models import (
    BrokerAccountSnapshot,
    BrokerBalanceSnapshot,
    BrokerConnectionSnapshot,
    BrokerOptionPositionSnapshot,
    BrokerPositionSnapshot,
    BrokerSyncRequest,
    BrokerSyncResult,
)


@runtime_checkable
class BrokerSyncService(Protocol):
    def list_connections(self, user_id: UUID) -> list[BrokerConnectionSnapshot]:
        """Return sanitized connection state without exposing credential material."""

    def list_accounts(self, broker_connection_id: UUID) -> list[BrokerAccountSnapshot]:
        """Return provider account mappings for a broker connection."""

    def get_balance_snapshot(self, broker_account_id: UUID) -> BrokerBalanceSnapshot | None:
        """Return the latest broker-provided balance snapshot, if available."""

    def get_position_snapshots(self, broker_account_id: UUID) -> list[BrokerPositionSnapshot]:
        """Return normalized stock/ETF position snapshots for a broker account."""

    def get_option_position_snapshots(self, broker_account_id: UUID) -> list[BrokerOptionPositionSnapshot]:
        """Return normalized option position snapshots for a broker account."""

    def request_sync(self, request: BrokerSyncRequest) -> BrokerSyncResult:
        """Create or start a read-only broker sync request."""
