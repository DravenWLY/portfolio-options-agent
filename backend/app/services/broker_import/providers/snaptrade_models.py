from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.broker_import import statuses
from app.services.broker_import.providers.models import (
    ProviderAccountSnapshot,
    ProviderBalanceSnapshot,
    ProviderConnectionSnapshot,
    ProviderOptionPositionSnapshot,
    ProviderPositionSnapshot,
    ProviderRefreshResult,
    ProviderTaxLotSnapshot,
    ProviderTransactionSnapshot,
)


class SnapTradeBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SnapTradeUserRegistrationResponse(SnapTradeBaseModel):
    snaptrade_user_id: str = Field(min_length=1)
    user_secret: str = Field(min_length=1)
    raw_payload: dict | None = None

    @field_validator("snaptrade_user_id", "user_secret")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return value.strip()


class SnapTradeConnectionPortalUrlResponse(SnapTradeBaseModel):
    portal_url: str = Field(min_length=1)
    expires_at: datetime | None = None
    raw_payload: dict | None = None


class SnapTradeConnectionResponse(SnapTradeBaseModel):
    provider: str = "snaptrade"
    broker_name: str = Field(min_length=1)
    provider_connection_id: str = Field(min_length=1)
    connection_status: str
    sync_status: str
    data_freshness_status: str
    sync_timestamp: datetime | None = None
    received_at: datetime
    raw_payload: dict | None = None

    @field_validator("connection_status")
    @classmethod
    def validate_connection_status(cls, value: str) -> str:
        if value not in statuses.CONNECTION_STATUSES:
            raise ValueError("connection_status is not supported")
        return value

    @field_validator("sync_status")
    @classmethod
    def validate_sync_status(cls, value: str) -> str:
        if value not in statuses.SYNC_STATUSES:
            raise ValueError("sync_status is not supported")
        return value

    @field_validator("data_freshness_status")
    @classmethod
    def validate_data_freshness_status(cls, value: str) -> str:
        if value not in statuses.DATA_FRESHNESS_STATUSES:
            raise ValueError("data_freshness_status is not supported")
        return value

    def to_provider_snapshot(self) -> ProviderConnectionSnapshot:
        return ProviderConnectionSnapshot(
            provider=self.provider,
            broker_name=self.broker_name,
            provider_connection_id=self.provider_connection_id,
            connection_status=self.connection_status,
            sync_status=self.sync_status,
            data_freshness_status=self.data_freshness_status,
            sync_timestamp=self.sync_timestamp,
            received_at=self.received_at,
            raw_payload=self.raw_payload,
        )


class SnapTradeAccountResponse(SnapTradeBaseModel):
    provider: str = "snaptrade"
    provider_connection_id: str = Field(min_length=1)
    provider_account_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    account_type: str = "other"
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    sync_status: str
    data_freshness_status: str
    sync_timestamp: datetime | None = None
    received_at: datetime
    raw_payload: dict | None = None

    @field_validator("base_currency")
    @classmethod
    def normalize_base_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("sync_status")
    @classmethod
    def validate_sync_status(cls, value: str) -> str:
        if value not in statuses.SYNC_STATUSES:
            raise ValueError("sync_status is not supported")
        return value

    @field_validator("data_freshness_status")
    @classmethod
    def validate_data_freshness_status(cls, value: str) -> str:
        if value not in statuses.DATA_FRESHNESS_STATUSES:
            raise ValueError("data_freshness_status is not supported")
        return value

    def to_provider_snapshot(self) -> ProviderAccountSnapshot:
        return ProviderAccountSnapshot(
            provider=self.provider,
            provider_connection_id=self.provider_connection_id,
            provider_account_id=self.provider_account_id,
            display_name=self.display_name,
            account_type=self.account_type,
            base_currency=self.base_currency,
            sync_status=self.sync_status,
            data_freshness_status=self.data_freshness_status,
            sync_timestamp=self.sync_timestamp,
            received_at=self.received_at,
            raw_payload=self.raw_payload,
        )


class SnapTradeBalanceResponse(SnapTradeBaseModel):
    provider: str = "snaptrade"
    provider_account_id: str = Field(min_length=1)
    total_cash: Decimal
    available_cash: Decimal | None = None
    buying_power: Decimal | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    sync_timestamp: datetime
    received_at: datetime
    sync_status: str
    data_freshness_status: str
    raw_payload: dict | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("sync_status")
    @classmethod
    def validate_sync_status(cls, value: str) -> str:
        if value not in statuses.SYNC_STATUSES:
            raise ValueError("sync_status is not supported")
        return value

    @field_validator("data_freshness_status")
    @classmethod
    def validate_data_freshness_status(cls, value: str) -> str:
        if value not in statuses.DATA_FRESHNESS_STATUSES:
            raise ValueError("data_freshness_status is not supported")
        return value

    def to_provider_snapshot(self) -> ProviderBalanceSnapshot:
        return ProviderBalanceSnapshot(
            provider=self.provider,
            provider_account_id=self.provider_account_id,
            total_cash=self.total_cash,
            available_cash=self.available_cash,
            buying_power=self.buying_power,
            currency=self.currency,
            sync_timestamp=self.sync_timestamp,
            received_at=self.received_at,
            sync_status=self.sync_status,
            data_freshness_status=self.data_freshness_status,
            raw_payload=self.raw_payload,
        )


class SnapTradeTaxLotResponse(SnapTradeBaseModel):
    acquired_date: date | None = None
    quantity: Decimal | None = None
    purchase_price: Decimal | None = None
    cost_basis: Decimal | None = None
    current_value: Decimal | None = None
    position_type: str | None = None

    def to_provider_snapshot(self) -> ProviderTaxLotSnapshot:
        return ProviderTaxLotSnapshot(
            acquired_date=self.acquired_date,
            quantity=self.quantity,
            purchase_price=self.purchase_price,
            cost_basis=self.cost_basis,
            current_value=self.current_value,
            position_type=self.position_type,
        )


class SnapTradePositionResponse(SnapTradeBaseModel):
    provider: str = "snaptrade"
    provider_account_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    asset_type: str
    quantity: Decimal
    market_value: Decimal | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    instrument_name: str | None = None
    market_price: Decimal | None = None
    average_purchase_price: Decimal | None = None
    open_pnl: Decimal | None = None
    tax_lots: tuple[SnapTradeTaxLotResponse, ...] = ()
    sync_timestamp: datetime
    received_at: datetime
    sync_status: str
    data_freshness_status: str
    raw_payload: dict | None = None

    @field_validator("symbol", "currency")
    @classmethod
    def normalize_uppercase(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("sync_status")
    @classmethod
    def validate_sync_status(cls, value: str) -> str:
        if value not in statuses.SYNC_STATUSES:
            raise ValueError("sync_status is not supported")
        return value

    @field_validator("data_freshness_status")
    @classmethod
    def validate_data_freshness_status(cls, value: str) -> str:
        if value not in statuses.DATA_FRESHNESS_STATUSES:
            raise ValueError("data_freshness_status is not supported")
        return value

    def to_provider_snapshot(self) -> ProviderPositionSnapshot:
        return ProviderPositionSnapshot(
            provider=self.provider,
            provider_account_id=self.provider_account_id,
            symbol=self.symbol,
            asset_type=self.asset_type,
            quantity=self.quantity,
            market_value=self.market_value,
            currency=self.currency,
            instrument_name=self.instrument_name,
            market_price=self.market_price,
            average_purchase_price=self.average_purchase_price,
            open_pnl=self.open_pnl,
            tax_lots=tuple(lot.to_provider_snapshot() for lot in self.tax_lots),
            sync_timestamp=self.sync_timestamp,
            received_at=self.received_at,
            sync_status=self.sync_status,
            data_freshness_status=self.data_freshness_status,
            raw_payload=self.raw_payload,
        )


class SnapTradeOptionPositionResponse(SnapTradeBaseModel):
    provider: str = "snaptrade"
    provider_account_id: str = Field(min_length=1)
    occ_symbol: str = Field(min_length=1)
    underlying_symbol: str = Field(min_length=1)
    position_side: str
    quantity: Decimal
    market_value: Decimal | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    market_price: Decimal | None = None
    average_purchase_price: Decimal | None = None
    open_pnl: Decimal | None = None
    multiplier: Decimal = Decimal("100")
    tax_lots: tuple[SnapTradeTaxLotResponse, ...] = ()
    sync_timestamp: datetime
    received_at: datetime
    sync_status: str
    data_freshness_status: str
    raw_payload: dict | None = None

    @field_validator("occ_symbol", "underlying_symbol", "currency")
    @classmethod
    def normalize_uppercase(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("position_side")
    @classmethod
    def validate_position_side(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"long", "short"}:
            raise ValueError("position_side must be long or short")
        return normalized

    @field_validator("sync_status")
    @classmethod
    def validate_sync_status(cls, value: str) -> str:
        if value not in statuses.SYNC_STATUSES:
            raise ValueError("sync_status is not supported")
        return value

    @field_validator("data_freshness_status")
    @classmethod
    def validate_data_freshness_status(cls, value: str) -> str:
        if value not in statuses.DATA_FRESHNESS_STATUSES:
            raise ValueError("data_freshness_status is not supported")
        return value

    def to_provider_snapshot(self) -> ProviderOptionPositionSnapshot:
        return ProviderOptionPositionSnapshot(
            provider=self.provider,
            provider_account_id=self.provider_account_id,
            occ_symbol=self.occ_symbol,
            underlying_symbol=self.underlying_symbol,
            position_side=self.position_side,
            quantity=self.quantity,
            market_value=self.market_value,
            currency=self.currency,
            market_price=self.market_price,
            average_purchase_price=self.average_purchase_price,
            open_pnl=self.open_pnl,
            multiplier=self.multiplier,
            tax_lots=tuple(lot.to_provider_snapshot() for lot in self.tax_lots),
            sync_timestamp=self.sync_timestamp,
            received_at=self.received_at,
            sync_status=self.sync_status,
            data_freshness_status=self.data_freshness_status,
            raw_payload=self.raw_payload,
        )


class SnapTradeTransactionResponse(SnapTradeBaseModel):
    provider: str = "snaptrade"
    provider_account_id: str = Field(min_length=1)
    provider_transaction_id: str = Field(min_length=1)
    transaction_type: str
    transaction_date: date
    symbol: str | None = None
    amount: Decimal | None = None
    quantity: Decimal | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    sync_timestamp: datetime
    received_at: datetime
    data_freshness_status: str
    raw_payload: dict | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_optional_symbol(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("data_freshness_status")
    @classmethod
    def validate_data_freshness_status(cls, value: str) -> str:
        if value not in statuses.DATA_FRESHNESS_STATUSES:
            raise ValueError("data_freshness_status is not supported")
        return value

    def to_provider_snapshot(self) -> ProviderTransactionSnapshot:
        return ProviderTransactionSnapshot(
            provider=self.provider,
            provider_account_id=self.provider_account_id,
            provider_transaction_id=self.provider_transaction_id,
            transaction_type=self.transaction_type,
            transaction_date=self.transaction_date,
            symbol=self.symbol,
            amount=self.amount,
            quantity=self.quantity,
            currency=self.currency,
            sync_timestamp=self.sync_timestamp,
            received_at=self.received_at,
            data_freshness_status=self.data_freshness_status,
            raw_payload=self.raw_payload,
        )


class SnapTradeRefreshResponse(SnapTradeBaseModel):
    provider: str = "snaptrade"
    provider_account_id: str = Field(min_length=1)
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    provider_request_id: str | None = None
    accounts_count: int = Field(default=0, ge=0)
    positions_count: int = Field(default=0, ge=0)
    transactions_count: int = Field(default=0, ge=0)
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    metadata: dict = Field(default_factory=dict)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in statuses.SYNC_RUN_STATUSES:
            raise ValueError("status is not supported")
        return value

    def to_provider_result(self) -> ProviderRefreshResult:
        return ProviderRefreshResult(
            provider=self.provider,
            provider_account_id=self.provider_account_id,
            status=self.status,
            started_at=self.started_at,
            completed_at=self.completed_at,
            provider_request_id=self.provider_request_id,
            accounts_count=self.accounts_count,
            positions_count=self.positions_count,
            transactions_count=self.transactions_count,
            warnings=self.warnings,
            errors=self.errors,
            metadata=self.metadata,
        )
