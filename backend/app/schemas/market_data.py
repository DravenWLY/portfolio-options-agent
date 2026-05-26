from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.services.market_data.models import (
    ActionabilityStatus,
    ContractSupportStatus,
    DataMode,
    FreshnessStatus,
    GreeksSource,
    ImpliedVolatilitySource,
    OptionType,
)


class QuoteFreshnessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    freshness_scope: Literal["market_quote"] = "market_quote"
    data_mode: DataMode
    freshness_status: FreshnessStatus
    actionability_status: ActionabilityStatus
    quote_age_seconds: int | None
    reason: str


class ProviderCapabilitiesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    supports_stock_quotes: bool
    supports_intraday_bars: bool
    supports_option_expirations: bool
    supports_option_chain: bool
    supports_option_snapshots: bool
    supports_iv: bool
    supports_greeks: bool
    supports_streaming: bool
    supports_historical_options: bool
    supported_data_modes: tuple[DataMode, ...]
    notes: tuple[str, ...]


class MarketDataProviderStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    freshness_scope: Literal["market_quote"] = "market_quote"
    data_mode: DataMode
    freshness_status: FreshnessStatus
    actionability_status: ActionabilityStatus
    checked_at: datetime
    capabilities: ProviderCapabilitiesRead
    message: str | None = None


class OptionContractIdentityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    underlying_symbol: str
    expiration_date: date
    strike: Decimal
    option_type: OptionType
    multiplier: Decimal
    occ_symbol: str | None
    provider_symbol: str | None
    provider_contract_id: str | None
    is_adjusted: bool
    is_mini: bool
    is_index: bool
    is_weekly: bool
    support_status: ContractSupportStatus
    unsupported_reason: str | None
    canonical_symbol: str
    requires_manual_review: bool


class StockQuoteSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    provider: str
    quote_time: datetime | None
    received_at: datetime
    data_mode: DataMode
    freshness_status: FreshnessStatus
    actionability_status: ActionabilityStatus
    currency: str = "USD"
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None
    mark: Decimal | None
    freshness_scope: Literal["market_quote"] = "market_quote"


class UnderlyingQuoteSnapshotRead(StockQuoteSnapshotRead):
    freshness_scope: Literal["underlying_quote"] = "underlying_quote"


class OptionQuoteSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contract: OptionContractIdentityRead
    provider: str
    quote_time: datetime | None
    received_at: datetime
    data_mode: DataMode
    freshness_status: FreshnessStatus
    actionability_status: ActionabilityStatus
    currency: str = "USD"
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None
    mark: Decimal | None
    volume: int | None
    open_interest: int | None
    implied_volatility: Decimal | None = Field(
        description="Implied volatility as a decimal fraction when supplied or calculated.",
    )
    delta: Decimal | None
    gamma: Decimal | None
    theta: Decimal | None
    vega: Decimal | None
    rho: Decimal | None
    underlying_price: Decimal | None
    underlying_quote_time: datetime | None
    implied_volatility_source: ImpliedVolatilitySource
    greeks_source: GreeksSource
    freshness_scope: Literal["option_quote"] = "option_quote"


class OptionChainSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    underlying_symbol: str
    provider: str
    expiration_date: date
    quote_time: datetime | None
    received_at: datetime
    data_mode: DataMode
    freshness_status: FreshnessStatus
    actionability_status: ActionabilityStatus
    contracts: tuple[OptionQuoteSnapshotRead, ...]
    underlying_quote: UnderlyingQuoteSnapshotRead | None
    freshness_scope: Literal["option_chain"] = "option_chain"
