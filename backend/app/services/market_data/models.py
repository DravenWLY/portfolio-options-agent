from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal


DataMode = Literal["live", "delayed", "indicative", "cached", "eod", "manual", "synthetic", "unavailable", "unknown"]
FreshnessStatus = Literal["fresh", "delayed", "stale", "eod_only", "manual", "unavailable", "unknown", "error"]
ActionabilityStatus = Literal[
    "actionable_snapshot",
    "analysis_only",
    "manual_review_required",
    "blocked_stale_quote",
    "blocked_unknown_quote",
    "blocked_provider_error",
]
ContractSupportStatus = Literal["supported", "manual_review_required", "unsupported"]
OptionType = Literal["call", "put"]
MarketMetricSource = Literal["provider", "calculated", "manual", "synthetic", "replay", "unavailable", "missing"]
GreeksSource = MarketMetricSource
ImpliedVolatilitySource = MarketMetricSource
MarketDataFreshnessScope = Literal["market_quote", "underlying_quote", "option_quote", "option_chain"]
MarketCoverageStatus = Literal["unknown", "limited_source", "unavailable"]

DATA_MODES: tuple[str, ...] = ("live", "delayed", "indicative", "cached", "eod", "manual", "synthetic", "unavailable", "unknown")
FRESHNESS_STATUSES: tuple[str, ...] = ("fresh", "delayed", "stale", "eod_only", "manual", "unavailable", "unknown", "error")
ACTIONABILITY_STATUSES: tuple[str, ...] = (
    "actionable_snapshot",
    "analysis_only",
    "manual_review_required",
    "blocked_stale_quote",
    "blocked_unknown_quote",
    "blocked_provider_error",
)
CONTRACT_SUPPORT_STATUSES: tuple[str, ...] = ("supported", "manual_review_required", "unsupported")
OPTION_TYPES: tuple[str, ...] = ("call", "put")
MARKET_METRIC_SOURCES: tuple[str, ...] = ("provider", "calculated", "manual", "synthetic", "replay", "unavailable", "missing")
GREEKS_SOURCES: tuple[str, ...] = MARKET_METRIC_SOURCES
IMPLIED_VOLATILITY_SOURCES: tuple[str, ...] = MARKET_METRIC_SOURCES
MARKET_COVERAGE_STATUSES: tuple[str, ...] = ("unknown", "limited_source", "unavailable")

MARKET_FRESHNESS_SCOPE = "market_quote"
UNDERLYING_QUOTE_FRESHNESS_SCOPE = "underlying_quote"
OPTION_QUOTE_FRESHNESS_SCOPE = "option_quote"
OPTION_CHAIN_FRESHNESS_SCOPE = "option_chain"


def _validate_choice(value: str, allowed: tuple[str, ...], field_name: str) -> None:
    if value not in allowed:
        allowed_values = ", ".join(allowed)
        raise ValueError(f"{field_name} must be one of: {allowed_values}")


def _validate_non_negative(value: Decimal | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_positive(value: Decimal, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol:
        raise ValueError("symbol must not be empty")
    return symbol


@dataclass(frozen=True)
class OptionContractIdentity:
    """Strategy-agnostic option identity across providers.

    The normalized identity is underlying + expiration + strike + call/put +
    multiplier. OCC symbol is preferred when available, but provider symbols and
    provider contract ids stay as metadata because each provider formats them
    differently. Adjusted, mini, index, and weekly contracts are flagged so
    strategy evaluators can require manual review when needed.
    """

    underlying_symbol: str
    expiration_date: date
    strike: Decimal
    option_type: OptionType
    multiplier: Decimal = Decimal("100")
    occ_symbol: str | None = None
    provider_symbol: str | None = None
    provider_contract_id: str | None = None
    is_adjusted: bool = False
    is_mini: bool = False
    is_index: bool = False
    is_weekly: bool = False
    support_status: ContractSupportStatus = "supported"
    unsupported_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "underlying_symbol", _normalize_symbol(self.underlying_symbol))
        if self.occ_symbol is not None:
            object.__setattr__(self, "occ_symbol", self.occ_symbol.strip().upper())
        if self.provider_symbol is not None:
            object.__setattr__(self, "provider_symbol", self.provider_symbol.strip())
        if self.provider_contract_id is not None:
            object.__setattr__(self, "provider_contract_id", self.provider_contract_id.strip())
        _validate_choice(self.option_type, OPTION_TYPES, "option_type")
        _validate_choice(self.support_status, CONTRACT_SUPPORT_STATUSES, "support_status")
        _validate_non_negative(self.strike, "strike")
        _validate_positive(self.multiplier, "multiplier")
        if self.support_status == "unsupported" and not self.unsupported_reason:
            raise ValueError("unsupported_reason is required when support_status is unsupported")

    @property
    def normalized_key(self) -> tuple[str, date, Decimal, str, Decimal]:
        return (
            self.underlying_symbol,
            self.expiration_date,
            self.strike,
            self.option_type,
            self.multiplier,
        )

    @property
    def canonical_symbol(self) -> str:
        if self.occ_symbol:
            return self.occ_symbol
        strike_text = format(self.strike.normalize(), "f")
        multiplier_text = format(self.multiplier.normalize(), "f")
        return f"{self.underlying_symbol}:{self.expiration_date.isoformat()}:{self.option_type}:{strike_text}:{multiplier_text}"

    @property
    def requires_manual_review(self) -> bool:
        return self.support_status != "supported" or self.is_adjusted or self.is_mini or self.is_index


@dataclass(frozen=True)
class QuoteRequestContext:
    symbols: tuple[str, ...] = ()
    option_symbols: tuple[str, ...] = ()
    requested_data_mode: DataMode = "unknown"
    max_age_seconds: int | None = None
    allow_cached: bool = True
    purpose: str = "analysis"

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbols", tuple(_normalize_symbol(symbol) for symbol in self.symbols))
        object.__setattr__(self, "option_symbols", tuple(symbol.strip().upper() for symbol in self.option_symbols))
        _validate_choice(self.requested_data_mode, DATA_MODES, "requested_data_mode")
        if self.max_age_seconds is not None and self.max_age_seconds < 0:
            raise ValueError("max_age_seconds must be non-negative")
        if not self.purpose.strip():
            raise ValueError("purpose must not be empty")


@dataclass(frozen=True)
class ProviderCapabilities:
    provider: str
    supports_stock_quotes: bool = False
    supports_intraday_bars: bool = False
    supports_option_expirations: bool = False
    supports_option_chain: bool = False
    supports_option_snapshots: bool = False
    supports_iv: bool = False
    supports_greeks: bool = False
    supports_streaming: bool = False
    supports_historical_options: bool = False
    supported_data_modes: tuple[DataMode, ...] = ("unknown",)
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        for data_mode in self.supported_data_modes:
            _validate_choice(data_mode, DATA_MODES, "supported_data_modes")


@dataclass(frozen=True)
class StockQuoteSnapshot:
    symbol: str
    provider: str
    quote_time: datetime | None
    received_at: datetime
    data_mode: DataMode
    freshness_status: FreshnessStatus
    actionability_status: ActionabilityStatus
    currency: str = "USD"
    bid: Decimal | None = None
    ask: Decimal | None = None
    last: Decimal | None = None
    mark: Decimal | None = None
    freshness_scope: Literal["market_quote"] = MARKET_FRESHNESS_SCOPE
    coverage_status: MarketCoverageStatus = "unknown"

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _normalize_symbol(self.symbol))
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        _validate_choice(self.data_mode, DATA_MODES, "data_mode")
        _validate_choice(self.freshness_status, FRESHNESS_STATUSES, "freshness_status")
        _validate_choice(self.actionability_status, ACTIONABILITY_STATUSES, "actionability_status")
        _validate_choice(self.coverage_status, MARKET_COVERAGE_STATUSES, "coverage_status")
        for field_name in ("bid", "ask", "last", "mark"):
            _validate_non_negative(getattr(self, field_name), field_name)


@dataclass(frozen=True)
class UnderlyingQuoteSnapshot(StockQuoteSnapshot):
    """Underlying quote used by option quotes and Greeks calculations."""

    freshness_scope: Literal["underlying_quote"] = UNDERLYING_QUOTE_FRESHNESS_SCOPE


@dataclass(frozen=True)
class OptionQuoteSnapshot:
    contract: OptionContractIdentity
    provider: str
    quote_time: datetime | None
    received_at: datetime
    data_mode: DataMode
    freshness_status: FreshnessStatus
    actionability_status: ActionabilityStatus
    currency: str = "USD"
    bid: Decimal | None = None
    ask: Decimal | None = None
    last: Decimal | None = None
    mark: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None
    implied_volatility: Decimal | None = None
    delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None
    rho: Decimal | None = None
    underlying_price: Decimal | None = None
    underlying_quote_time: datetime | None = None
    implied_volatility_source: ImpliedVolatilitySource = "missing"
    greeks_source: GreeksSource = "missing"
    freshness_scope: Literal["option_quote"] = OPTION_QUOTE_FRESHNESS_SCOPE
    coverage_status: MarketCoverageStatus = "unknown"

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        _validate_choice(self.data_mode, DATA_MODES, "data_mode")
        _validate_choice(self.freshness_status, FRESHNESS_STATUSES, "freshness_status")
        _validate_choice(self.actionability_status, ACTIONABILITY_STATUSES, "actionability_status")
        _validate_choice(self.implied_volatility_source, IMPLIED_VOLATILITY_SOURCES, "implied_volatility_source")
        _validate_choice(self.greeks_source, GREEKS_SOURCES, "greeks_source")
        _validate_choice(self.coverage_status, MARKET_COVERAGE_STATUSES, "coverage_status")
        for field_name in ("bid", "ask", "last", "mark", "implied_volatility", "gamma", "underlying_price"):
            _validate_non_negative(getattr(self, field_name), field_name)
        for field_name in ("volume", "open_interest"):
            value = getattr(self, field_name)
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True)
class OptionChainSnapshot:
    underlying_symbol: str
    provider: str
    expiration_date: date
    quote_time: datetime | None
    received_at: datetime
    data_mode: DataMode
    freshness_status: FreshnessStatus
    actionability_status: ActionabilityStatus
    contracts: tuple[OptionQuoteSnapshot, ...] = field(default_factory=tuple)
    underlying_quote: UnderlyingQuoteSnapshot | None = None
    freshness_scope: Literal["option_chain"] = OPTION_CHAIN_FRESHNESS_SCOPE
    coverage_status: MarketCoverageStatus = "unknown"

    def __post_init__(self) -> None:
        object.__setattr__(self, "underlying_symbol", _normalize_symbol(self.underlying_symbol))
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        _validate_choice(self.data_mode, DATA_MODES, "data_mode")
        _validate_choice(self.freshness_status, FRESHNESS_STATUSES, "freshness_status")
        _validate_choice(self.actionability_status, ACTIONABILITY_STATUSES, "actionability_status")
        _validate_choice(self.coverage_status, MARKET_COVERAGE_STATUSES, "coverage_status")
        object.__setattr__(self, "contracts", tuple(self.contracts))
        for option_quote in self.contracts:
            if option_quote.contract.underlying_symbol != self.underlying_symbol:
                raise ValueError("all option contracts must match chain underlying_symbol")
            if option_quote.contract.expiration_date != self.expiration_date:
                raise ValueError("all option contracts must match chain expiration_date")
