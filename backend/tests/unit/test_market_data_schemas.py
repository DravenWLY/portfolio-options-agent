from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.schemas.market_data import (
    MarketDataProviderStatusRead,
    OptionChainSnapshotRead,
    OptionContractIdentityRead,
    OptionQuoteSnapshotRead,
    ProviderCapabilitiesRead,
    QuoteFreshnessRead,
    StockQuoteSnapshotRead,
    UnderlyingQuoteSnapshotRead,
)
from app.services.market_data import (
    OptionChainSnapshot,
    OptionContractIdentity,
    OptionQuoteSnapshot,
    ProviderCapabilities,
    StockQuoteSnapshot,
    UnderlyingQuoteSnapshot,
    evaluate_quote_freshness,
)


pytestmark = [pytest.mark.unit]


FORBIDDEN_BROKER_FIELDS = {
    "account_id",
    "broker_account_id",
    "broker_connection_id",
    "cash_balance_id",
    "provider_account_id",
    "provider_connection_id",
    "total_cash",
    "available_cash",
    "buying_power",
    "positions",
    "holdings",
    "secret_ref",
    "encrypted_secret_ref",
    "raw_payload",
    "raw_metadata",
}


def test_market_data_schema_field_sets_are_exact() -> None:
    assert set(QuoteFreshnessRead.model_fields) == {
        "freshness_scope",
        "data_mode",
        "freshness_status",
        "actionability_status",
        "quote_age_seconds",
        "reason",
    }
    assert set(ProviderCapabilitiesRead.model_fields) == {
        "provider",
        "supports_stock_quotes",
        "supports_intraday_bars",
        "supports_option_expirations",
        "supports_option_chain",
        "supports_option_snapshots",
        "supports_iv",
        "supports_greeks",
        "supports_streaming",
        "supports_historical_options",
        "supported_data_modes",
        "notes",
    }
    assert set(MarketDataProviderStatusRead.model_fields) == {
        "provider",
        "freshness_scope",
        "data_mode",
        "freshness_status",
        "actionability_status",
        "checked_at",
        "capabilities",
        "message",
    }
    assert set(StockQuoteSnapshotRead.model_fields) == {
        "symbol",
        "provider",
        "quote_time",
        "received_at",
        "data_mode",
        "freshness_status",
        "actionability_status",
        "currency",
        "bid",
        "ask",
        "last",
        "mark",
        "freshness_scope",
        "coverage_status",
    }
    assert set(OptionContractIdentityRead.model_fields) == {
        "underlying_symbol",
        "expiration_date",
        "strike",
        "option_type",
        "multiplier",
        "occ_symbol",
        "provider_symbol",
        "provider_contract_id",
        "is_adjusted",
        "is_mini",
        "is_index",
        "is_weekly",
        "support_status",
        "unsupported_reason",
        "canonical_symbol",
        "requires_manual_review",
    }
    assert set(OptionQuoteSnapshotRead.model_fields) == {
        "contract",
        "provider",
        "quote_time",
        "received_at",
        "data_mode",
        "freshness_status",
        "actionability_status",
        "currency",
        "bid",
        "ask",
        "last",
        "mark",
        "volume",
        "open_interest",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
        "underlying_price",
        "underlying_quote_time",
        "implied_volatility_source",
        "greeks_source",
        "freshness_scope",
        "coverage_status",
    }
    assert set(OptionChainSnapshotRead.model_fields) == {
        "underlying_symbol",
        "provider",
        "expiration_date",
        "quote_time",
        "received_at",
        "data_mode",
        "freshness_status",
        "actionability_status",
        "contracts",
        "underlying_quote",
        "freshness_scope",
        "coverage_status",
    }


def test_market_data_schemas_do_not_contain_broker_or_cash_fields() -> None:
    schemas = [
        QuoteFreshnessRead,
        ProviderCapabilitiesRead,
        MarketDataProviderStatusRead,
        StockQuoteSnapshotRead,
        UnderlyingQuoteSnapshotRead,
        OptionContractIdentityRead,
        OptionQuoteSnapshotRead,
        OptionChainSnapshotRead,
    ]

    for schema in schemas:
        assert FORBIDDEN_BROKER_FIELDS.isdisjoint(set(schema.model_fields)), schema.__name__


def test_market_data_schemas_validate_domain_objects() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    contract = OptionContractIdentity(
        underlying_symbol="HOOD",
        expiration_date=date(2026, 6, 18),
        strike=Decimal("85"),
        option_type="call",
        occ_symbol="HOOD260618C00085000",
    )
    option_quote = OptionQuoteSnapshot(
        contract=contract,
        provider="manual",
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
        mark=Decimal("2.90"),
        greeks_source="manual",
    )
    chain = OptionChainSnapshot(
        underlying_symbol="HOOD",
        provider="manual",
        expiration_date=date(2026, 6, 18),
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
        contracts=(option_quote,),
    )

    quote_read = OptionQuoteSnapshotRead.model_validate(option_quote)
    chain_read = OptionChainSnapshotRead.model_validate(chain)

    assert quote_read.freshness_scope == "option_quote"
    assert quote_read.contract.canonical_symbol == "HOOD260618C00085000"
    assert len(chain_read.contracts) == 1
    assert chain_read.freshness_scope == "option_chain"


def test_provider_status_schema_keeps_market_quote_scope() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    capabilities = ProviderCapabilities(provider="manual", supports_stock_quotes=True, supported_data_modes=("manual",))
    decision = evaluate_quote_freshness(
        data_mode="manual",
        quote_time=None,
        received_at=now,
        now=now,
    )

    status = MarketDataProviderStatusRead(
        provider="manual",
        data_mode=decision.data_mode,
        freshness_status=decision.freshness_status,
        actionability_status=decision.actionability_status,
        checked_at=now,
        capabilities=ProviderCapabilitiesRead.model_validate(capabilities),
        message=decision.reason,
    )

    assert status.freshness_scope == "market_quote"
    assert status.capabilities.supports_stock_quotes is True


def test_stock_quote_schema_serializes_market_quote_snapshot() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    quote = StockQuoteSnapshot(
        symbol="VOO",
        provider="manual",
        quote_time=now,
        received_at=now,
        data_mode="manual",
        freshness_status="manual",
        actionability_status="manual_review_required",
        last=Decimal("500.00"),
    )

    payload = StockQuoteSnapshotRead.model_validate(quote).model_dump()

    assert payload["symbol"] == "VOO"
    assert payload["freshness_scope"] == "market_quote"


def test_underlying_quote_schema_keeps_underlying_freshness_scope_distinct() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    quote = UnderlyingQuoteSnapshot(
        symbol="VOO",
        provider="manual",
        quote_time=now,
        received_at=now,
        data_mode="synthetic",
        freshness_status="fresh",
        actionability_status="analysis_only",
        last=Decimal("500.00"),
    )

    payload = UnderlyingQuoteSnapshotRead.model_validate(quote).model_dump()

    assert payload["freshness_scope"] == "underlying_quote"
    assert payload["data_mode"] == "synthetic"
