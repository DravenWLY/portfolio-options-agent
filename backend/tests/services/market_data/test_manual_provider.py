from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.services.market_data import (
    ManualMarketDataNotFoundError,
    ManualMarketDataProvider,
    MarketDataProvider,
    OptionContractIdentity,
    OptionDataProvider,
    build_manual_option_quote,
    build_manual_stock_quote,
)


pytestmark = [pytest.mark.unit]


def _demo_contract() -> OptionContractIdentity:
    return OptionContractIdentity(
        underlying_symbol="HOOD",
        expiration_date=date(2026, 6, 18),
        strike=Decimal("85"),
        option_type="call",
        occ_symbol="HOOD260618C00085000",
    )


def test_manual_provider_satisfies_market_and_option_protocols() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    contract = _demo_contract()
    stock_quote = build_manual_stock_quote(symbol="HOOD", received_at=now, now=now, last=Decimal("77.14"))
    option_quote = build_manual_option_quote(
        contract=contract,
        received_at=now,
        now=now,
        mark=Decimal("2.90"),
        delta=Decimal("0.30"),
    )
    provider = ManualMarketDataProvider(stock_quotes=(stock_quote,), option_quotes=(option_quote,))

    assert isinstance(provider, MarketDataProvider)
    assert isinstance(provider, OptionDataProvider)
    assert provider.get_capabilities().provider == "manual"
    assert provider.get_stock_quote("hood").symbol == "HOOD"
    assert provider.get_underlying_quote("hood").freshness_scope == "underlying_quote"
    assert provider.get_option_quote(contract).mark == Decimal("2.90")
    assert provider.get_option_quote_with_greeks(contract).delta == Decimal("0.30")


def test_manual_provider_builds_chain_from_explicit_option_quotes() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    contract = _demo_contract()
    option_quote = build_manual_option_quote(contract=contract, received_at=now, now=now, mark=Decimal("2.90"))
    provider = ManualMarketDataProvider(option_quotes=(option_quote,))

    chain = provider.get_option_chain("hood", date(2026, 6, 18))

    assert provider.get_option_expirations("hood") == [date(2026, 6, 18)]
    assert chain.underlying_symbol == "HOOD"
    assert len(chain.contracts) == 1


def test_manual_provider_supports_synthetic_delayed_indicative_stale_eod_unavailable_and_unknown_modes() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    synthetic = build_manual_stock_quote(
        symbol="SYNTH",
        received_at=now,
        quote_time=now,
        now=now,
        data_mode="synthetic",
    )
    delayed = build_manual_stock_quote(
        symbol="DELAY",
        received_at=now,
        quote_time=now - timedelta(minutes=5),
        now=now,
        data_mode="delayed",
    )
    indicative = build_manual_stock_quote(
        symbol="INDICATIVE",
        received_at=now,
        quote_time=now,
        now=now,
        data_mode="indicative",
    )
    stale = build_manual_stock_quote(
        symbol="STALE",
        received_at=now,
        quote_time=now - timedelta(hours=2),
        now=now,
        data_mode="cached",
        max_age_seconds=60,
    )
    eod = build_manual_stock_quote(
        symbol="EOD",
        received_at=now,
        quote_time=now - timedelta(hours=8),
        now=now,
        data_mode="eod",
    )
    unknown = build_manual_stock_quote(
        symbol="UNKNOWN",
        received_at=now,
        quote_time=None,
        now=now,
        data_mode="unknown",
    )
    unavailable = build_manual_stock_quote(
        symbol="UNAVAILABLE",
        received_at=now,
        quote_time=None,
        now=now,
        data_mode="unavailable",
    )

    assert synthetic.freshness_status == "fresh"
    assert synthetic.actionability_status == "analysis_only"
    assert delayed.freshness_status == "delayed"
    assert delayed.actionability_status == "analysis_only"
    assert indicative.freshness_status == "fresh"
    assert indicative.actionability_status == "analysis_only"
    assert stale.freshness_status == "stale"
    assert stale.actionability_status == "blocked_stale_quote"
    assert eod.freshness_status == "eod_only"
    assert unknown.freshness_status == "unknown"
    assert unavailable.freshness_status == "unavailable"
    assert unavailable.actionability_status == "blocked_unknown_quote"


def test_manual_provider_builders_never_create_actionable_snapshots() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    contract = _demo_contract()

    for data_mode in ("manual", "synthetic", "delayed", "indicative", "cached", "eod", "unavailable", "unknown"):
        stock_quote = build_manual_stock_quote(
            symbol=f"DEMO-{data_mode}",
            received_at=now,
            quote_time=now,
            now=now,
            data_mode=data_mode,
        )
        option_quote = build_manual_option_quote(
            contract=contract,
            received_at=now,
            quote_time=now,
            now=now,
            data_mode=data_mode,
        )

        assert stock_quote.actionability_status != "actionable_snapshot"
        assert option_quote.actionability_status != "actionable_snapshot"


def test_manual_provider_builders_reject_live_data_mode() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    contract = _demo_contract()

    with pytest.raises(ValueError, match="manual provider data_mode"):
        build_manual_stock_quote(
            symbol="LIVE",
            received_at=now,
            quote_time=now,
            now=now,
            data_mode="live",
        )

    with pytest.raises(ValueError, match="manual provider data_mode"):
        build_manual_option_quote(
            contract=contract,
            received_at=now,
            quote_time=now,
            now=now,
            data_mode="live",
        )


def test_manual_provider_missing_quotes_raise_safe_lookup_error() -> None:
    provider = ManualMarketDataProvider()

    with pytest.raises(ManualMarketDataNotFoundError, match="manual stock quote not found"):
        provider.get_stock_quote("MISSING")

    with pytest.raises(ManualMarketDataNotFoundError, match="manual option chain not found"):
        provider.get_option_chain("HOOD", date(2026, 6, 18))
