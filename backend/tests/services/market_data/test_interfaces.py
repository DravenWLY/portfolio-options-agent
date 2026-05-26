from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.services.market_data import (
    GreeksProvider,
    MarketDataProvider,
    OptionChainSnapshot,
    OptionContractIdentity,
    OptionDataProvider,
    OptionQuoteSnapshot,
    ProviderCapabilities,
    QuoteRequestContext,
    StockQuoteSnapshot,
    UnderlyingQuoteSnapshot,
)


pytestmark = [pytest.mark.unit]


class FakeMarketDataProvider:
    def __init__(self) -> None:
        self.now = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider="manual",
            supports_stock_quotes=True,
            supports_intraday_bars=True,
            supported_data_modes=("manual",),
        )

    def get_stock_quote(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> StockQuoteSnapshot:
        return StockQuoteSnapshot(
            symbol=symbol,
            provider="manual",
            quote_time=self.now,
            received_at=self.now,
            data_mode=context.requested_data_mode if context else "manual",
            freshness_status="manual",
            actionability_status="manual_review_required",
            last=Decimal("100"),
        )

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
        return UnderlyingQuoteSnapshot(
            symbol=symbol,
            provider="manual",
            quote_time=self.now,
            received_at=self.now,
            data_mode=context.requested_data_mode if context else "manual",
            freshness_status="manual",
            actionability_status="manual_review_required",
            last=Decimal("100"),
        )

    def get_intraday_bars(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> list[StockQuoteSnapshot]:
        return [self.get_stock_quote(symbol, context)]


class FakeOptionDataProvider:
    def __init__(self) -> None:
        self.now = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)
        self.contract = OptionContractIdentity(
            underlying_symbol="HOOD",
            expiration_date=date(2026, 6, 18),
            strike=Decimal("85"),
            option_type="call",
            occ_symbol="HOOD260618C00085000",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider="manual",
            supports_option_expirations=True,
            supports_option_chain=True,
            supports_option_snapshots=True,
            supported_data_modes=("manual",),
        )

    def get_option_expirations(
        self,
        underlying_symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> list[date]:
        return [self.contract.expiration_date]

    def get_option_quote(
        self,
        contract: OptionContractIdentity,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        return OptionQuoteSnapshot(
            contract=contract,
            provider="manual",
            quote_time=self.now,
            received_at=self.now,
            data_mode=context.requested_data_mode if context else "manual",
            freshness_status="manual",
            actionability_status="manual_review_required",
            bid=Decimal("2.80"),
            ask=Decimal("3.00"),
            mark=Decimal("2.90"),
        )

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
        quote = self.get_option_quote(self.contract, context)
        return OptionChainSnapshot(
            underlying_symbol=underlying_symbol,
            provider="manual",
            expiration_date=expiration_date,
            quote_time=self.now,
            received_at=self.now,
            data_mode=context.requested_data_mode if context else "manual",
            freshness_status="manual",
            actionability_status="manual_review_required",
            contracts=(quote,),
        )


class FakeGreeksProvider:
    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider="manual",
            supports_greeks=True,
            supported_data_modes=("manual",),
        )

    def get_option_quote_with_greeks(
        self,
        contract: OptionContractIdentity,
        underlying_quote: UnderlyingQuoteSnapshot | None = None,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        now = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)
        return OptionQuoteSnapshot(
            contract=contract,
            provider="manual",
            quote_time=now,
            received_at=now,
            data_mode=context.requested_data_mode if context else "manual",
            freshness_status="manual",
            actionability_status="manual_review_required",
            delta=Decimal("0.30"),
            gamma=Decimal("0.01"),
            theta=Decimal("-0.04"),
            vega=Decimal("0.12"),
            rho=Decimal("0.03"),
            greeks_source="manual",
        )

    def calculate_greeks(
        self,
        quote: OptionQuoteSnapshot,
        underlying_quote: UnderlyingQuoteSnapshot | None = None,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        return quote


def test_fake_market_data_provider_satisfies_protocol() -> None:
    provider = FakeMarketDataProvider()
    context = QuoteRequestContext(symbols=("hood",), requested_data_mode="manual")

    assert isinstance(provider, MarketDataProvider)
    assert provider.get_capabilities().supports_stock_quotes is True
    assert provider.get_stock_quote("hood", context).symbol == "HOOD"
    assert provider.get_underlying_quote("hood", context).freshness_scope == "underlying_quote"
    assert len(provider.get_intraday_bars("hood", context)) == 1


def test_fake_option_data_provider_satisfies_protocol() -> None:
    provider = FakeOptionDataProvider()
    context = QuoteRequestContext(option_symbols=("hood260618c00085000",), requested_data_mode="manual")

    assert isinstance(provider, OptionDataProvider)
    assert provider.get_capabilities().supports_option_chain is True
    assert provider.get_option_expirations("HOOD", context) == [date(2026, 6, 18)]
    assert provider.get_option_quote(provider.contract, context).contract.canonical_symbol == "HOOD260618C00085000"
    assert len(provider.get_option_chain("HOOD", date(2026, 6, 18), context).contracts) == 1


def test_fake_greeks_provider_satisfies_protocol() -> None:
    option_provider = FakeOptionDataProvider()
    greeks_provider = FakeGreeksProvider()
    context = QuoteRequestContext(option_symbols=("hood260618c00085000",), requested_data_mode="manual")

    assert isinstance(greeks_provider, GreeksProvider)
    quote = greeks_provider.get_option_quote_with_greeks(option_provider.contract, context=context)

    assert quote.greeks_source == "manual"
    assert quote.delta == Decimal("0.30")


def test_market_data_interfaces_do_not_expose_strategy_or_trading_methods() -> None:
    disallowed_methods = {
        "place_order",
        "submit_order",
        "cancel_order",
        "execute_trade",
        "screen_cash_secured_puts",
        "screen_covered_calls",
        "run_wheel_strategy",
    }

    exposed = set(MarketDataProvider.__dict__) | set(OptionDataProvider.__dict__) | set(GreeksProvider.__dict__)

    assert disallowed_methods.isdisjoint(exposed)
