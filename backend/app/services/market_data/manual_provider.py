from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal

from app.services.market_data.freshness import DEFAULT_MAX_QUOTE_AGE_SECONDS, evaluate_quote_freshness
from app.services.market_data.interfaces import GreeksProvider, MarketDataProvider, OptionDataProvider
from app.services.market_data.models import (
    DataMode,
    GreeksSource,
    ImpliedVolatilitySource,
    MarketMetricSource,
    OptionChainSnapshot,
    OptionContractIdentity,
    OptionQuoteSnapshot,
    ProviderCapabilities,
    QuoteRequestContext,
    StockQuoteSnapshot,
    UnderlyingQuoteSnapshot,
)


MANUAL_PROVIDER_DATA_MODES: tuple[DataMode, ...] = (
    "manual",
    "synthetic",
    "delayed",
    "indicative",
    "cached",
    "eod",
    "unavailable",
    "unknown",
)


class ManualMarketDataNotFoundError(LookupError):
    """Raised when the manual provider has no explicit synthetic input."""


class ManualMarketDataProvider(MarketDataProvider, OptionDataProvider, GreeksProvider):
    """Deterministic in-memory provider for manual or synthetic/replay fixtures."""

    provider_name = "manual"

    def __init__(
        self,
        *,
        stock_quotes: Iterable[StockQuoteSnapshot] = (),
        option_quotes: Iterable[OptionQuoteSnapshot] = (),
        option_chains: Iterable[OptionChainSnapshot] = (),
    ) -> None:
        self._stock_quotes = {quote.symbol: quote for quote in stock_quotes}
        self._option_quotes = {quote.contract.canonical_symbol: quote for quote in option_quotes}
        self._option_chains = {
            (chain.underlying_symbol, chain.expiration_date): chain for chain in option_chains
        }

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=self.provider_name,
            supports_stock_quotes=True,
            supports_intraday_bars=False,
            supports_option_expirations=True,
            supports_option_chain=True,
            supports_option_snapshots=True,
            supports_iv=True,
            supports_greeks=True,
            supports_streaming=False,
            supports_historical_options=False,
            supported_data_modes=MANUAL_PROVIDER_DATA_MODES,
            notes=("Manual/synthetic replay provider; no network calls.",),
        )

    def get_stock_quote(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> StockQuoteSnapshot:
        key = symbol.strip().upper()
        try:
            return self._stock_quotes[key]
        except KeyError as exc:
            raise ManualMarketDataNotFoundError(f"manual stock quote not found for {key}") from exc

    def get_stock_quotes(
        self,
        symbols: list[str],
        context: QuoteRequestContext | None = None,
    ) -> list[StockQuoteSnapshot]:
        return [self.get_stock_quote(symbol, context) for symbol in symbols]

    def get_underlying_quote(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> UnderlyingQuoteSnapshot:
        stock_quote = self.get_stock_quote(symbol, context)
        return UnderlyingQuoteSnapshot(
            symbol=stock_quote.symbol,
            provider=stock_quote.provider,
            quote_time=stock_quote.quote_time,
            received_at=stock_quote.received_at,
            data_mode=stock_quote.data_mode,
            freshness_status=stock_quote.freshness_status,
            actionability_status=stock_quote.actionability_status,
            currency=stock_quote.currency,
            bid=stock_quote.bid,
            ask=stock_quote.ask,
            last=stock_quote.last,
            mark=stock_quote.mark,
        )

    def get_intraday_bars(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> list[StockQuoteSnapshot]:
        return [self.get_stock_quote(symbol, context)]

    def get_option_expirations(
        self,
        underlying_symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> list[date]:
        underlying = underlying_symbol.strip().upper()
        expirations = {
            quote.contract.expiration_date
            for quote in self._option_quotes.values()
            if quote.contract.underlying_symbol == underlying
        }
        expirations.update(
            expiration for chain_underlying, expiration in self._option_chains if chain_underlying == underlying
        )
        return sorted(expirations)

    def get_option_quote(
        self,
        contract: OptionContractIdentity,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        try:
            return self._option_quotes[contract.canonical_symbol]
        except KeyError as exc:
            raise ManualMarketDataNotFoundError(
                f"manual option quote not found for {contract.canonical_symbol}"
            ) from exc

    def get_option_quotes(
        self,
        contracts: list[OptionContractIdentity],
        context: QuoteRequestContext | None = None,
    ) -> list[OptionQuoteSnapshot]:
        return [self.get_option_quote(contract, context) for contract in contracts]

    def get_option_chain(
        self,
        underlying_symbol: str,
        expiration_date: date,
        context: QuoteRequestContext | None = None,
    ) -> OptionChainSnapshot:
        key = (underlying_symbol.strip().upper(), expiration_date)
        try:
            return self._option_chains[key]
        except KeyError:
            quotes = [
                quote
                for quote in self._option_quotes.values()
                if quote.contract.underlying_symbol == key[0] and quote.contract.expiration_date == expiration_date
            ]
            if not quotes:
                raise ManualMarketDataNotFoundError(
                    f"manual option chain not found for {key[0]} {expiration_date.isoformat()}"
                )
            first_quote = quotes[0]
            return OptionChainSnapshot(
                underlying_symbol=key[0],
                provider=self.provider_name,
                expiration_date=expiration_date,
                quote_time=first_quote.quote_time,
                received_at=first_quote.received_at,
                data_mode=first_quote.data_mode,
                freshness_status=first_quote.freshness_status,
                actionability_status=first_quote.actionability_status,
                contracts=tuple(quotes),
            )

    def get_option_quote_with_greeks(
        self,
        contract: OptionContractIdentity,
        underlying_quote: UnderlyingQuoteSnapshot | None = None,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        return self.get_option_quote(contract, context)

    def calculate_greeks(
        self,
        quote: OptionQuoteSnapshot,
        underlying_quote: UnderlyingQuoteSnapshot | None = None,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        return quote


def build_manual_stock_quote(
    *,
    symbol: str,
    received_at: datetime,
    quote_time: datetime | None = None,
    now: datetime | None = None,
    data_mode: DataMode = "manual",
    currency: str = "USD",
    bid: Decimal | None = None,
    ask: Decimal | None = None,
    last: Decimal | None = None,
    mark: Decimal | None = None,
    max_age_seconds: int = DEFAULT_MAX_QUOTE_AGE_SECONDS,
) -> StockQuoteSnapshot:
    _validate_manual_provider_data_mode(data_mode)
    decision = evaluate_quote_freshness(
        data_mode=data_mode,
        quote_time=quote_time,
        received_at=received_at,
        now=now,
        max_age_seconds=max_age_seconds,
    )
    return StockQuoteSnapshot(
        symbol=symbol,
        provider=ManualMarketDataProvider.provider_name,
        quote_time=quote_time,
        received_at=received_at,
        data_mode=data_mode,
        freshness_status=decision.freshness_status,
        actionability_status=decision.actionability_status,
        currency=currency,
        bid=bid,
        ask=ask,
        last=last,
        mark=mark,
    )


def build_manual_option_quote(
    *,
    contract: OptionContractIdentity,
    received_at: datetime,
    quote_time: datetime | None = None,
    now: datetime | None = None,
    data_mode: DataMode = "manual",
    currency: str = "USD",
    bid: Decimal | None = None,
    ask: Decimal | None = None,
    last: Decimal | None = None,
    mark: Decimal | None = None,
    volume: int | None = None,
    open_interest: int | None = None,
    implied_volatility: Decimal | None = None,
    delta: Decimal | None = None,
    gamma: Decimal | None = None,
    theta: Decimal | None = None,
    vega: Decimal | None = None,
    rho: Decimal | None = None,
    underlying_price: Decimal | None = None,
    underlying_quote_time: datetime | None = None,
    implied_volatility_source: ImpliedVolatilitySource | None = None,
    greeks_source: GreeksSource | None = None,
    max_age_seconds: int = DEFAULT_MAX_QUOTE_AGE_SECONDS,
) -> OptionQuoteSnapshot:
    _validate_manual_provider_data_mode(data_mode)
    decision = evaluate_quote_freshness(
        data_mode=data_mode,
        quote_time=quote_time,
        received_at=received_at,
        now=now,
        max_age_seconds=max_age_seconds,
        manual_review_required=contract.requires_manual_review,
    )
    return OptionQuoteSnapshot(
        contract=contract,
        provider=ManualMarketDataProvider.provider_name,
        quote_time=quote_time,
        received_at=received_at,
        data_mode=data_mode,
        freshness_status=decision.freshness_status,
        actionability_status=decision.actionability_status,
        currency=currency,
        bid=bid,
        ask=ask,
        last=last,
        mark=mark,
        volume=volume,
        open_interest=open_interest,
        implied_volatility=implied_volatility,
        delta=delta,
        gamma=gamma,
        theta=theta,
        vega=vega,
        rho=rho,
        underlying_price=underlying_price,
        underlying_quote_time=underlying_quote_time,
        implied_volatility_source=implied_volatility_source
        or _fixture_metric_source(data_mode, value_available=implied_volatility is not None),
        greeks_source=greeks_source
        or _fixture_metric_source(data_mode, value_available=any(value is not None for value in (delta, gamma, theta, vega, rho))),
    )


def _validate_manual_provider_data_mode(data_mode: DataMode) -> None:
    if data_mode not in MANUAL_PROVIDER_DATA_MODES:
        allowed = ", ".join(MANUAL_PROVIDER_DATA_MODES)
        raise ValueError(f"manual provider data_mode must be one of: {allowed}")


def _fixture_metric_source(data_mode: DataMode, *, value_available: bool) -> MarketMetricSource:
    if data_mode == "unavailable":
        return "unavailable"
    if not value_available:
        return "missing"
    if data_mode == "synthetic":
        return "synthetic"
    return "manual"
