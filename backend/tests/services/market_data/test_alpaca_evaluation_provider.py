from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.schemas.risk import MarketDataSnapshotReferenceRead
from app.services.market_data import (
    AlpacaBasicEvaluationProvider,
    OptionContractIdentity,
    option_chain_snapshot_reference,
    option_quote_snapshot_reference,
)


pytestmark = [pytest.mark.unit]


NOW = datetime(2026, 5, 26, 15, 0, tzinfo=UTC)
EXPIRATION = date(2026, 6, 19)


def _contract() -> OptionContractIdentity:
    return OptionContractIdentity(
        underlying_symbol="DEMO",
        expiration_date=EXPIRATION,
        strike=Decimal("50"),
        option_type="call",
        occ_symbol="DEMO260619C00050000",
    )


def _option_payload(timestamp: datetime = NOW) -> dict[str, object]:
    return {
        "symbol": "DEMO260619C00050000",
        "strike_price": "50",
        "option_type": "call",
        "timestamp": timestamp,
        "bid_price": "1.10",
        "ask_price": "1.30",
        "mark_price": "1.20",
        "volume": 20,
        "open_interest": 100,
        "implied_volatility": "0.31",
        "delta": "0.41",
        "gamma": "0.02",
        "theta": "-0.03",
        "vega": "0.09",
        "rho": "0.01",
    }


class FakeAlpacaClient:
    def __init__(
        self,
        *,
        stock_payload: dict[str, object] | None = None,
        option_payload: dict[str, object] | None = None,
        chain_payloads: tuple[dict[str, object], ...] | None = None,
        fail: bool = False,
    ) -> None:
        self.stock_payload = stock_payload or {
            "timestamp": NOW,
            "bid_price": "49.90",
            "ask_price": "50.10",
            "last_price": "50.00",
        }
        self.option_payload = option_payload if option_payload is not None else _option_payload()
        self.chain_payloads = chain_payloads if chain_payloads is not None else (_option_payload(),)
        self.fail = fail
        self.calls: list[str] = []

    def fetch_stock_quote(self, symbol: str) -> dict[str, object] | None:
        self.calls.append(f"stock:{symbol}")
        self._maybe_fail()
        return self.stock_payload

    def fetch_option_quote(self, option_symbol: str) -> dict[str, object] | None:
        self.calls.append(f"option:{option_symbol}")
        self._maybe_fail()
        return self.option_payload

    def fetch_option_chain(self, underlying_symbol: str, expiration_date: date) -> tuple[dict[str, object], ...]:
        self.calls.append(f"chain:{underlying_symbol}:{expiration_date.isoformat()}")
        self._maybe_fail()
        return self.chain_payloads

    def fetch_option_expirations(self, underlying_symbol: str) -> tuple[date, ...]:
        self.calls.append(f"expirations:{underlying_symbol}")
        self._maybe_fail()
        return (EXPIRATION,)

    def _maybe_fail(self) -> None:
        if self.fail:
            raise RuntimeError("synthetic raw provider detail must not escape")


def _provider(client: FakeAlpacaClient) -> AlpacaBasicEvaluationProvider:
    return AlpacaBasicEvaluationProvider(client=client, clock=lambda: NOW)


def test_capabilities_and_underlying_quote_are_injected_indicative_and_limited_source() -> None:
    client = FakeAlpacaClient()
    provider = _provider(client)

    capabilities = provider.get_capabilities()
    assert client.calls == []
    quote = provider.get_underlying_quote("demo")

    assert capabilities.supported_data_modes == ("indicative", "unavailable")
    assert client.calls == ["stock:DEMO"]
    assert quote.freshness_scope == "underlying_quote"
    assert quote.data_mode == "indicative"
    assert quote.coverage_status == "limited_source"
    assert quote.actionability_status == "analysis_only"
    assert quote.actionability_status != "actionable_snapshot"


def test_option_quote_maps_available_provider_metrics_without_inventing_values() -> None:
    quote = _provider(FakeAlpacaClient()).get_option_quote(_contract())

    assert quote.freshness_scope == "option_quote"
    assert quote.data_mode == "indicative"
    assert quote.coverage_status == "limited_source"
    assert quote.implied_volatility == Decimal("0.31")
    assert quote.implied_volatility_source == "provider"
    assert quote.greeks_source == "provider"
    assert quote.actionability_status == "analysis_only"


def test_option_chain_reference_preserves_granular_scope_and_limited_source_coverage() -> None:
    chain = _provider(FakeAlpacaClient()).get_option_chain("DEMO", EXPIRATION)
    reference = option_chain_snapshot_reference(
        chain,
        snapshot_id="alpaca-evaluation-chain",
        purpose="report_input_snapshot",
    )
    read = MarketDataSnapshotReferenceRead.model_validate(reference)

    assert chain.freshness_scope == "option_chain"
    assert chain.data_mode == "indicative"
    assert chain.coverage_status == "limited_source"
    assert len(chain.contracts) == 1
    assert read.freshness_scope == "market_quote"
    assert read.input_freshness_scope == "option_chain"
    assert read.coverage_status == "limited_source"


def test_malformed_provider_symbol_does_not_cross_contract_or_reference_boundary() -> None:
    payload = _option_payload()
    payload["symbol"] = "provider-contract-demo-123"
    chain = _provider(FakeAlpacaClient(chain_payloads=(payload,))).get_option_chain("DEMO", EXPIRATION)
    quote = chain.contracts[0]
    reference = option_quote_snapshot_reference(
        quote,
        snapshot_id="alpaca-evaluation-option",
        purpose="report_input_snapshot",
    )

    assert quote.contract.occ_symbol is None
    assert quote.contract.canonical_symbol == "DEMO:2026-06-19:call:50:100"
    assert reference.stable_key == "DEMO:2026-06-19:call:50:100"
    assert "provider-contract" not in reference.stable_key


def test_missing_and_incomplete_option_inputs_are_unavailable_not_fabricated() -> None:
    client = FakeAlpacaClient(
        option_payload={"timestamp": NOW},
        chain_payloads=({"timestamp": NOW, "strike_price": "50"},),
    )
    provider = _provider(client)

    quote = provider.get_option_quote(_contract())
    chain = provider.get_option_chain("DEMO", EXPIRATION)

    assert quote.data_mode == "unavailable"
    assert quote.coverage_status == "unavailable"
    assert quote.actionability_status == "blocked_unknown_quote"
    assert quote.implied_volatility is None
    assert quote.implied_volatility_source == "unavailable"
    assert quote.greeks_source == "unavailable"
    assert chain.data_mode == "unavailable"
    assert chain.coverage_status == "unavailable"
    assert chain.actionability_status == "blocked_unknown_quote"


def test_malformed_and_non_finite_quote_numbers_degrade_without_raising() -> None:
    client = FakeAlpacaClient(
        stock_payload={"timestamp": NOW, "last_price": "not-a-number"},
        option_payload={"timestamp": NOW, "bid_price": "NaN"},
        chain_payloads=(
            {
                "symbol": "DEMO260619C00050000",
                "strike_price": "Infinity",
                "option_type": "call",
                "timestamp": NOW,
                "mark_price": "1.20",
            },
        ),
    )
    provider = _provider(client)

    underlying = provider.get_underlying_quote("DEMO")
    option_quote = provider.get_option_quote(_contract())
    chain = provider.get_option_chain("DEMO", EXPIRATION)

    for snapshot in (underlying, option_quote, chain):
        assert snapshot.data_mode == "unavailable"
        assert snapshot.coverage_status == "unavailable"
        assert snapshot.actionability_status == "blocked_unknown_quote"


def test_present_quote_with_absent_iv_and_greeks_records_missing_provenance() -> None:
    payload = {
        "timestamp": NOW,
        "bid_price": "1.10",
        "ask_price": "1.30",
    }
    quote = _provider(FakeAlpacaClient(option_payload=payload)).get_option_quote(_contract())

    assert quote.coverage_status == "limited_source"
    assert quote.implied_volatility is None
    assert quote.implied_volatility_source == "missing"
    assert quote.greeks_source == "missing"
    assert quote.actionability_status == "analysis_only"


def test_stale_indicative_input_is_blocked_under_existing_freshness_policy() -> None:
    client = FakeAlpacaClient(
        stock_payload={
            "timestamp": NOW - timedelta(hours=1),
            "last_price": "50.00",
        }
    )
    quote = _provider(client).get_underlying_quote("DEMO")

    assert quote.data_mode == "indicative"
    assert quote.coverage_status == "limited_source"
    assert quote.freshness_status == "stale"
    assert quote.actionability_status == "blocked_stale_quote"


def test_injected_client_failure_returns_sanitized_blocked_snapshot() -> None:
    quote = _provider(FakeAlpacaClient(fail=True)).get_option_quote(_contract())

    rendered = repr(quote).lower()
    assert quote.data_mode == "unavailable"
    assert quote.coverage_status == "unavailable"
    assert quote.freshness_status == "error"
    assert quote.actionability_status == "blocked_provider_error"
    assert "raw provider detail" not in rendered
    assert "runtimeerror" not in rendered
