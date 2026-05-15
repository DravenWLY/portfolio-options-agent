from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.services.broker_import import statuses


def _validate_choice(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    if value not in allowed:
        allowed_values = ", ".join(allowed)
        raise ValueError(f"{field_name} must be one of: {allowed_values}")


@dataclass(frozen=True)
class BrokerSyncRequest:
    broker_connection_id: UUID
    broker_account_id: UUID | None = None
    trigger: str = "manual"
    force_refresh: bool = False

    def __post_init__(self) -> None:
        allowed_triggers = ("manual", "scheduled", "webhook", "retry", "system")
        _validate_choice(self.trigger, allowed_triggers, "trigger")


@dataclass(frozen=True)
class BrokerConnectionSnapshot:
    provider: str
    broker_name: str
    provider_connection_id: str
    connection_status: str
    sync_status: str
    data_freshness_status: str
    synced_at: datetime | None = None
    received_at: datetime | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_choice(self.connection_status, statuses.CONNECTION_STATUSES, "connection_status")
        _validate_choice(self.sync_status, statuses.SYNC_STATUSES, "sync_status")
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class BrokerAccountSnapshot:
    provider_account_id: str
    display_name: str
    account_type: str
    base_currency: str
    sync_status: str
    data_freshness_status: str
    synced_at: datetime | None = None
    received_at: datetime | None = None
    raw_payload: dict | None = None

    def __post_init__(self) -> None:
        _validate_choice(self.sync_status, statuses.SYNC_STATUSES, "sync_status")
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class BrokerBalanceSnapshot:
    provider_account_id: str
    total_cash: Decimal
    available_cash: Decimal | None
    buying_power: Decimal | None
    currency: str
    synced_at: datetime
    data_freshness_status: str

    def __post_init__(self) -> None:
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class BrokerPositionSnapshot:
    provider_account_id: str
    symbol: str
    quantity: Decimal
    asset_type: str
    market_value: Decimal | None
    currency: str
    synced_at: datetime
    data_freshness_status: str
    raw_payload: dict | None = None

    def __post_init__(self) -> None:
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class BrokerOptionPositionSnapshot:
    provider_account_id: str
    occ_symbol: str
    underlying_symbol: str
    position_side: str
    quantity: Decimal
    market_value: Decimal | None
    currency: str
    synced_at: datetime
    data_freshness_status: str
    raw_payload: dict | None = None

    def __post_init__(self) -> None:
        _validate_choice(self.position_side, ("long", "short"), "position_side")
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class BrokerSyncResult:
    broker_connection_id: UUID
    broker_account_id: UUID | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    accounts_count: int = 0
    positions_count: int = 0
    transactions_count: int = 0
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_choice(self.status, statuses.SYNC_RUN_STATUSES, "status")
        if self.started_at is not None and self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must be after started_at")
        for field_name in ("accounts_count", "positions_count", "transactions_count"):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be non-negative")
