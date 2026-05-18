from datetime import date
from typing import Protocol, Sequence, runtime_checkable

from app.services.market_data.models import (
    OptionChainSnapshot,
    OptionContractIdentity,
    OptionQuoteSnapshot,
    ProviderCapabilities,
    QuoteRequestContext,
    StockQuoteSnapshot,
    UnderlyingQuoteSnapshot,
)


@runtime_checkable
class MarketDataProvider(Protocol):
    def get_capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities without making a quote request."""

    def get_stock_quote(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> StockQuoteSnapshot:
        """Return one stock or ETF quote snapshot."""

    def get_stock_quotes(
        self,
        symbols: Sequence[str],
        context: QuoteRequestContext | None = None,
    ) -> list[StockQuoteSnapshot]:
        """Return stock or ETF quote snapshots for a batch of symbols."""

    def get_underlying_quote(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> UnderlyingQuoteSnapshot:
        """Return an underlying quote snapshot suitable for option analysis."""

    def get_intraday_bars(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> list[StockQuoteSnapshot]:
        """Return intraday quote/bar-like snapshots when the provider supports them."""


@runtime_checkable
class OptionDataProvider(Protocol):
    def get_capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities without making an option-chain request."""

    def get_option_expirations(
        self,
        underlying_symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> list[date]:
        """Return option expiration dates for an underlying symbol."""

    def get_option_quote(
        self,
        contract: OptionContractIdentity,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        """Return one option quote snapshot."""

    def get_option_quotes(
        self,
        contracts: Sequence[OptionContractIdentity],
        context: QuoteRequestContext | None = None,
    ) -> list[OptionQuoteSnapshot]:
        """Return option quote snapshots for a batch of contracts."""

    def get_option_chain(
        self,
        underlying_symbol: str,
        expiration_date: date,
        context: QuoteRequestContext | None = None,
    ) -> OptionChainSnapshot:
        """Return an option chain snapshot for one underlying and expiration."""


@runtime_checkable
class GreeksProvider(Protocol):
    def get_capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities without making a Greeks request."""

    def get_option_quote_with_greeks(
        self,
        contract: OptionContractIdentity,
        underlying_quote: UnderlyingQuoteSnapshot | None = None,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        """Return one option quote snapshot with provider or calculated Greeks."""

    def calculate_greeks(
        self,
        quote: OptionQuoteSnapshot,
        underlying_quote: UnderlyingQuoteSnapshot | None = None,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        """Return a quote snapshot enriched with calculated Greeks."""
