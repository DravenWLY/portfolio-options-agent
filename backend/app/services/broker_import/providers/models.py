from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from app.services.broker_import import statuses


def _validate_choice(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    if value not in allowed:
        allowed_values = ", ".join(allowed)
        raise ValueError(f"{field_name} must be one of: {allowed_values}")


@dataclass(frozen=True)
class ProviderConnectionSnapshot:
    provider: str
    broker_name: str
    provider_connection_id: str
    connection_status: str
    sync_status: str
    data_freshness_status: str
    sync_timestamp: datetime | None
    received_at: datetime
    warnings: tuple[str, ...] = ()
    raw_payload: dict | None = None

    def __post_init__(self) -> None:
        _validate_choice(self.connection_status, statuses.CONNECTION_STATUSES, "connection_status")
        _validate_choice(self.sync_status, statuses.SYNC_STATUSES, "sync_status")
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class ProviderAccountSnapshot:
    provider: str
    provider_connection_id: str
    provider_account_id: str
    display_name: str
    account_type: str
    base_currency: str
    sync_status: str
    data_freshness_status: str
    sync_timestamp: datetime | None
    received_at: datetime
    raw_payload: dict | None = None

    def __post_init__(self) -> None:
        _validate_choice(self.sync_status, statuses.SYNC_STATUSES, "sync_status")
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class ProviderBalanceSnapshot:
    provider: str
    provider_account_id: str
    total_cash: Decimal
    available_cash: Decimal | None
    buying_power: Decimal | None
    currency: str
    sync_timestamp: datetime
    received_at: datetime
    sync_status: str
    data_freshness_status: str
    raw_payload: dict | None = None

    def __post_init__(self) -> None:
        _validate_choice(self.sync_status, statuses.SYNC_STATUSES, "sync_status")
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class ProviderTaxLotSnapshot:
    acquired_date: date | None
    quantity: Decimal | None
    purchase_price: Decimal | None
    cost_basis: Decimal | None
    current_value: Decimal | None
    position_type: str | None = None


@dataclass(frozen=True)
class ProviderPositionSnapshot:
    provider: str
    provider_account_id: str
    symbol: str
    asset_type: str
    quantity: Decimal
    market_value: Decimal | None
    currency: str
    sync_timestamp: datetime
    received_at: datetime
    sync_status: str
    data_freshness_status: str
    instrument_name: str | None = None
    market_price: Decimal | None = None
    average_purchase_price: Decimal | None = None
    open_pnl: Decimal | None = None
    tax_lots: tuple[ProviderTaxLotSnapshot, ...] = ()
    raw_payload: dict | None = None

    def __post_init__(self) -> None:
        _validate_choice(self.sync_status, statuses.SYNC_STATUSES, "sync_status")
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class ProviderOptionPositionSnapshot:
    provider: str
    provider_account_id: str
    occ_symbol: str
    underlying_symbol: str
    position_side: str
    quantity: Decimal
    market_value: Decimal | None
    currency: str
    sync_timestamp: datetime
    received_at: datetime
    sync_status: str
    data_freshness_status: str
    market_price: Decimal | None = None
    average_purchase_price: Decimal | None = None
    open_pnl: Decimal | None = None
    multiplier: Decimal = Decimal("100")
    tax_lots: tuple[ProviderTaxLotSnapshot, ...] = ()
    raw_payload: dict | None = None

    def __post_init__(self) -> None:
        _validate_choice(self.position_side, ("long", "short"), "position_side")
        _validate_choice(self.sync_status, statuses.SYNC_STATUSES, "sync_status")
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class ProviderTransactionSnapshot:
    provider: str
    provider_account_id: str
    provider_transaction_id: str
    transaction_type: str
    transaction_date: date
    symbol: str | None
    amount: Decimal | None
    quantity: Decimal | None
    currency: str
    sync_timestamp: datetime
    received_at: datetime
    data_freshness_status: str
    raw_payload: dict | None = None

    def __post_init__(self) -> None:
        _validate_choice(self.data_freshness_status, statuses.DATA_FRESHNESS_STATUSES, "data_freshness_status")


@dataclass(frozen=True)
class ProviderRefreshResult:
    provider: str
    provider_account_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    provider_request_id: str | None = None
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
