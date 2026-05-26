from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.services.market_data import (
    ACTIONABILITY_STATUSES,
    DATA_MODES,
    FRESHNESS_STATUSES,
    OptionChainSnapshot,
    OptionContractIdentity,
    OptionQuoteSnapshot,
    ProviderCapabilities,
    QuoteRequestContext,
    StockQuoteSnapshot,
    UnderlyingQuoteSnapshot,
)


pytestmark = [pytest.mark.unit]


def test_market_data_vocabulary_contains_actionability_and_freshness_values() -> None:
    assert "live" in DATA_MODES
    assert "manual" in DATA_MODES
    assert "synthetic" in DATA_MODES
    assert "unavailable" in DATA_MODES
    assert "eod_only" in FRESHNESS_STATUSES
    assert "unavailable" in FRESHNESS_STATUSES
    assert "blocked_stale_quote" in ACTIONABILITY_STATUSES
    assert "blocked_provider_error" in ACTIONABILITY_STATUSES


def test_option_contract_identity_prefers_occ_symbol_and_normalizes_key() -> None:
    contract = OptionContractIdentity(
        underlying_symbol=" voo ",
        expiration_date=date(2026, 1, 16),
        strike=Decimal("400"),
        option_type="put",
        occ_symbol="voo260116p00400000",
        provider_symbol="provider-specific-id",
    )

    assert contract.underlying_symbol == "VOO"
    assert contract.occ_symbol == "VOO260116P00400000"
    assert contract.canonical_symbol == "VOO260116P00400000"
    assert contract.normalized_key == (
        "VOO",
        date(2026, 1, 16),
        Decimal("400"),
        "put",
        Decimal("100"),
    )


def test_option_contract_identity_flags_manual_review_contracts() -> None:
    adjusted_contract = OptionContractIdentity(
        underlying_symbol="SPX",
        expiration_date=date(2026, 6, 19),
        strike=Decimal("5000"),
        option_type="call",
        is_index=True,
        support_status="manual_review_required",
    )

    assert adjusted_contract.requires_manual_review is True

    with pytest.raises(ValueError, match="unsupported_reason"):
        OptionContractIdentity(
            underlying_symbol="DEMO",
            expiration_date=date(2026, 6, 19),
            strike=Decimal("10"),
            option_type="call",
            support_status="unsupported",
        )


def test_stock_and_underlying_quote_snapshots_are_market_quote_scoped() -> None:
    now = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)
    stock_quote = StockQuoteSnapshot(
        symbol="hood",
        provider="manual",
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
        bid=Decimal("77.10"),
        ask=Decimal("77.20"),
        last=Decimal("77.14"),
        mark=Decimal("77.15"),
    )
    underlying_quote = UnderlyingQuoteSnapshot(
        symbol="HOOD",
        provider="manual",
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
        last=Decimal("77.14"),
    )

    assert stock_quote.symbol == "HOOD"
    assert stock_quote.freshness_scope == "market_quote"
    assert underlying_quote.freshness_scope == "underlying_quote"


def test_option_quote_snapshot_keeps_contract_and_quote_freshness_separate() -> None:
    now = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)
    contract = OptionContractIdentity(
        underlying_symbol="HOOD",
        expiration_date=date(2026, 6, 18),
        strike=Decimal("85"),
        option_type="call",
        occ_symbol="HOOD260618C00085000",
    )
    quote = OptionQuoteSnapshot(
        contract=contract,
        provider="manual",
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
        bid=Decimal("2.80"),
        ask=Decimal("3.00"),
        last=Decimal("2.90"),
        volume=125,
        open_interest=2500,
        implied_volatility=Decimal("0.55"),
        delta=Decimal("0.30"),
        gamma=Decimal("0.01"),
        theta=Decimal("-0.04"),
        vega=Decimal("0.12"),
        rho=Decimal("0.03"),
        underlying_price=Decimal("77.14"),
        greeks_source="manual",
    )

    assert quote.contract.canonical_symbol == "HOOD260618C00085000"
    assert quote.freshness_scope == "option_quote"
    assert quote.actionability_status == "manual_review_required"


def test_option_chain_snapshot_rejects_mismatched_contracts() -> None:
    now = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)
    matching_contract = OptionContractIdentity(
        underlying_symbol="VOO",
        expiration_date=date(2026, 1, 16),
        strike=Decimal("400"),
        option_type="put",
    )
    mismatched_contract = OptionContractIdentity(
        underlying_symbol="QQQ",
        expiration_date=date(2026, 1, 16),
        strike=Decimal("350"),
        option_type="put",
    )
    matching_quote = OptionQuoteSnapshot(
        contract=matching_contract,
        provider="manual",
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
    )
    mismatched_quote = OptionQuoteSnapshot(
        contract=mismatched_contract,
        provider="manual",
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
    )

    chain = OptionChainSnapshot(
        underlying_symbol="VOO",
        provider="manual",
        expiration_date=date(2026, 1, 16),
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
        contracts=(matching_quote,),
    )
    assert len(chain.contracts) == 1

    with pytest.raises(ValueError, match="underlying_symbol"):
        OptionChainSnapshot(
            underlying_symbol="VOO",
            provider="manual",
            expiration_date=date(2026, 1, 16),
            quote_time=now,
            received_at=now,
            data_mode="manual",
            freshness_status="manual",
            actionability_status="manual_review_required",
            contracts=(mismatched_quote,),
        )


def test_provider_capabilities_and_request_context_are_provider_agnostic() -> None:
    capabilities = ProviderCapabilities(
        provider="manual",
        supports_stock_quotes=True,
        supports_option_chain=True,
        supports_greeks=True,
        supported_data_modes=("manual", "cached"),
    )
    request = QuoteRequestContext(
        symbols=("hood", "voo"),
        option_symbols=("hood260618c00085000",),
        requested_data_mode="manual",
        max_age_seconds=900,
        allow_cached=True,
        purpose="risk_analysis",
    )

    assert capabilities.supports_option_chain is True
    assert capabilities.supported_data_modes == ("manual", "cached")
    assert request.symbols == ("HOOD", "VOO")
    assert request.option_symbols == ("HOOD260618C00085000",)


def test_domain_models_reject_invalid_values() -> None:
    now = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="data_mode"):
        StockQuoteSnapshot(
            symbol="VOO",
            provider="manual",
            quote_time=now,
            received_at=now,
            data_mode="broker_sync",
            freshness_status="manual",
            actionability_status="manual_review_required",
        )

    with pytest.raises(ValueError, match="strike"):
        OptionContractIdentity(
            underlying_symbol="VOO",
            expiration_date=date(2026, 1, 16),
            strike=Decimal("-1"),
            option_type="put",
        )
