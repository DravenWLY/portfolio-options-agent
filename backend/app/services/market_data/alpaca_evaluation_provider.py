"""Offline Alpaca Basic-shaped mapping adapter for local/internal evaluation.

The adapter has no transport or credential behavior. Callers must inject a
client boundary; default tests use fixed synthetic payloads only.
"""

import re
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Protocol

from app.services.market_data.freshness import QuoteFreshnessDecision, evaluate_quote_freshness
from app.services.market_data.interfaces import MarketDataProvider, OptionDataProvider
from app.services.market_data.models import (
    MarketCoverageStatus,
    MarketDataFreshnessScope,
    OptionChainSnapshot,
    OptionContractIdentity,
    OptionQuoteSnapshot,
    ProviderCapabilities,
    QuoteRequestContext,
    StockQuoteSnapshot,
    UnderlyingQuoteSnapshot,
)


ALPACA_BASIC_EVALUATION_PROVIDER = "alpaca_basic_evaluation"
_NORMALIZED_OCC_SYMBOL_PATTERN = re.compile(
    r"^(?P<underlying>[A-Z]{1,6})(?P<expiration>\d{6})(?P<option_type>[CP])(?P<strike>\d{8})$"
)


class AlpacaEvaluationClient(Protocol):
    """Injected payload boundary; no network implementation is provided here."""

    def fetch_stock_quote(self, symbol: str) -> Mapping[str, object] | None: ...

    def fetch_option_quote(self, option_symbol: str) -> Mapping[str, object] | None: ...

    def fetch_option_chain(self, underlying_symbol: str, expiration_date: date) -> Sequence[Mapping[str, object]]: ...

    def fetch_option_expirations(self, underlying_symbol: str) -> Sequence[date]: ...


class AlpacaBasicEvaluationProvider(MarketDataProvider, OptionDataProvider):
    """Map injected Alpaca Basic-shaped fixtures into app-owned snapshots."""

    provider_name = ALPACA_BASIC_EVALUATION_PROVIDER

    def __init__(
        self,
        *,
        client: AlpacaEvaluationClient,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._client = client
        self._clock = clock or (lambda: datetime.now(UTC))

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider=self.provider_name,
            supports_stock_quotes=True,
            supports_option_expirations=True,
            supports_option_chain=True,
            supports_option_snapshots=True,
            supports_iv=True,
            supports_greeks=True,
            supports_streaming=False,
            supports_historical_options=False,
            supported_data_modes=("indicative", "unavailable"),
            notes=("Injected-fixture evaluation adapter; indicative limited-source output only.",),
        )

    def get_stock_quote(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> StockQuoteSnapshot:
        return self._get_equity_quote(symbol, scope="market_quote", underlying=False)

    def get_stock_quotes(
        self,
        symbols: Sequence[str],
        context: QuoteRequestContext | None = None,
    ) -> list[StockQuoteSnapshot]:
        return [self.get_stock_quote(symbol, context) for symbol in symbols]

    def get_underlying_quote(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> UnderlyingQuoteSnapshot:
        return self._get_equity_quote(symbol, scope="underlying_quote", underlying=True)

    def get_intraday_bars(
        self,
        symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> list[StockQuoteSnapshot]:
        return []

    def get_option_expirations(
        self,
        underlying_symbol: str,
        context: QuoteRequestContext | None = None,
    ) -> list[date]:
        try:
            return sorted(set(self._client.fetch_option_expirations(underlying_symbol.strip().upper())))
        except Exception:
            return []

    def get_option_quote(
        self,
        contract: OptionContractIdentity,
        context: QuoteRequestContext | None = None,
    ) -> OptionQuoteSnapshot:
        now = self._clock()
        try:
            payload = self._client.fetch_option_quote(contract.canonical_symbol)
        except Exception:
            return self._map_option_quote(contract, None, now=now, provider_error=True)
        return self._map_option_quote(contract, payload, now=now)

    def get_option_quotes(
        self,
        contracts: Sequence[OptionContractIdentity],
        context: QuoteRequestContext | None = None,
    ) -> list[OptionQuoteSnapshot]:
        return [self.get_option_quote(contract, context) for contract in contracts]

    def get_option_chain(
        self,
        underlying_symbol: str,
        expiration_date: date,
        context: QuoteRequestContext | None = None,
    ) -> OptionChainSnapshot:
        underlying = underlying_symbol.strip().upper()
        now = self._clock()
        try:
            payloads = tuple(self._client.fetch_option_chain(underlying, expiration_date))
        except Exception:
            return self._unavailable_chain(underlying, expiration_date, now=now, provider_error=True)

        quotes: list[OptionQuoteSnapshot] = []
        incomplete = False
        for payload in payloads:
            contract = _contract_from_chain_payload(payload, underlying, expiration_date)
            if contract is None:
                incomplete = True
                continue
            quote = self._map_option_quote(contract, payload, now=now)
            quotes.append(quote)
            incomplete = incomplete or quote.coverage_status == "unavailable"

        if not quotes or incomplete:
            return self._unavailable_chain(
                underlying,
                expiration_date,
                now=now,
                contracts=tuple(quotes),
            )

        quote_time = min(quote.quote_time for quote in quotes if quote.quote_time is not None)
        decision = evaluate_quote_freshness(
            data_mode="indicative",
            quote_time=quote_time,
            received_at=now,
            now=now,
            freshness_scope="option_chain",
        )
        return OptionChainSnapshot(
            underlying_symbol=underlying,
            provider=self.provider_name,
            expiration_date=expiration_date,
            quote_time=quote_time,
            received_at=now,
            data_mode="indicative",
            freshness_status=decision.freshness_status,
            actionability_status=decision.actionability_status,
            contracts=tuple(quotes),
            coverage_status="limited_source",
        )

    def _get_equity_quote(
        self,
        symbol: str,
        *,
        scope: MarketDataFreshnessScope,
        underlying: bool,
    ) -> StockQuoteSnapshot | UnderlyingQuoteSnapshot:
        now = self._clock()
        try:
            payload = self._client.fetch_stock_quote(symbol.strip().upper())
        except Exception:
            payload = None
            provider_error = True
        else:
            provider_error = False

        quote_time, coverage_status, decision = _input_decision(
            payload,
            now=now,
            scope=scope,
            provider_error=provider_error,
        )
        snapshot_type = UnderlyingQuoteSnapshot if underlying else StockQuoteSnapshot
        return snapshot_type(
            symbol=symbol,
            provider=self.provider_name,
            quote_time=quote_time,
            received_at=now,
            data_mode=decision.data_mode,
            freshness_status=decision.freshness_status,
            actionability_status=decision.actionability_status,
            bid=_decimal_field(payload, "bid_price") if coverage_status != "unavailable" else None,
            ask=_decimal_field(payload, "ask_price") if coverage_status != "unavailable" else None,
            last=_decimal_field(payload, "last_price") if coverage_status != "unavailable" else None,
            mark=_decimal_field(payload, "mark_price") if coverage_status != "unavailable" else None,
            coverage_status=coverage_status,
        )

    def _map_option_quote(
        self,
        contract: OptionContractIdentity,
        payload: Mapping[str, object] | None,
        *,
        now: datetime,
        provider_error: bool = False,
    ) -> OptionQuoteSnapshot:
        quote_time, coverage_status, decision = _input_decision(
            payload,
            now=now,
            scope="option_quote",
            provider_error=provider_error,
        )
        available = coverage_status != "unavailable"
        implied_volatility = _decimal_field(payload, "implied_volatility") if available else None
        greeks = {
            name: _decimal_field(payload, name) if available else None
            for name in ("delta", "gamma", "theta", "vega", "rho")
        }
        return OptionQuoteSnapshot(
            contract=contract,
            provider=self.provider_name,
            quote_time=quote_time,
            received_at=now,
            data_mode=decision.data_mode,
            freshness_status=decision.freshness_status,
            actionability_status=decision.actionability_status,
            bid=_decimal_field(payload, "bid_price") if available else None,
            ask=_decimal_field(payload, "ask_price") if available else None,
            last=_decimal_field(payload, "last_price") if available else None,
            mark=_decimal_field(payload, "mark_price") if available else None,
            volume=_int_field(payload, "volume") if available else None,
            open_interest=_int_field(payload, "open_interest") if available else None,
            implied_volatility=implied_volatility,
            delta=greeks["delta"],
            gamma=greeks["gamma"],
            theta=greeks["theta"],
            vega=greeks["vega"],
            rho=greeks["rho"],
            implied_volatility_source="provider" if implied_volatility is not None else ("unavailable" if not available else "missing"),
            greeks_source="provider" if any(value is not None for value in greeks.values()) else ("unavailable" if not available else "missing"),
            coverage_status=coverage_status,
        )

    def _unavailable_chain(
        self,
        underlying_symbol: str,
        expiration_date: date,
        *,
        now: datetime,
        contracts: tuple[OptionQuoteSnapshot, ...] = (),
        provider_error: bool = False,
    ) -> OptionChainSnapshot:
        decision = evaluate_quote_freshness(
            data_mode="unavailable",
            quote_time=None,
            received_at=now,
            now=now,
            provider_error=provider_error,
            freshness_scope="option_chain",
        )
        return OptionChainSnapshot(
            underlying_symbol=underlying_symbol,
            provider=self.provider_name,
            expiration_date=expiration_date,
            quote_time=None,
            received_at=now,
            data_mode=decision.data_mode,
            freshness_status=decision.freshness_status,
            actionability_status=decision.actionability_status,
            contracts=contracts,
            coverage_status="unavailable",
        )


def _input_decision(
    payload: Mapping[str, object] | None,
    *,
    now: datetime,
    scope: MarketDataFreshnessScope,
    provider_error: bool,
) -> tuple[datetime | None, MarketCoverageStatus, QuoteFreshnessDecision]:
    quote_time = _datetime_field(payload, "timestamp")
    has_quote_value = any(
        _decimal_field(payload, field_name) is not None
        for field_name in ("bid_price", "ask_price", "last_price", "mark_price")
    )
    data_mode = "indicative" if quote_time is not None and has_quote_value and not provider_error else "unavailable"
    coverage_status: MarketCoverageStatus = "limited_source" if data_mode == "indicative" else "unavailable"
    decision = evaluate_quote_freshness(
        data_mode=data_mode,
        quote_time=quote_time if data_mode == "indicative" else None,
        received_at=now,
        now=now,
        provider_error=provider_error,
        freshness_scope=scope,
    )
    return quote_time if data_mode == "indicative" else None, coverage_status, decision


def _contract_from_chain_payload(
    payload: Mapping[str, object],
    underlying_symbol: str,
    expiration_date: date,
) -> OptionContractIdentity | None:
    strike = _decimal_field(payload, "strike_price")
    option_type = payload.get("option_type")
    if strike is None or option_type not in {"call", "put"}:
        return None
    symbol = payload.get("symbol")
    occ_symbol = _validated_occ_symbol(
        symbol,
        underlying_symbol=underlying_symbol,
        expiration_date=expiration_date,
        strike=strike,
        option_type=option_type,
    )
    return OptionContractIdentity(
        underlying_symbol=underlying_symbol,
        expiration_date=expiration_date,
        strike=strike,
        option_type=option_type,
        occ_symbol=occ_symbol,
    )


def _validated_occ_symbol(
    value: object,
    *,
    underlying_symbol: str,
    expiration_date: date,
    strike: Decimal,
    option_type: str,
) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    match = _NORMALIZED_OCC_SYMBOL_PATTERN.fullmatch(normalized)
    if match is None:
        return None
    encoded_strike = Decimal(match.group("strike")) / Decimal("1000")
    if (
        match.group("underlying") != underlying_symbol
        or match.group("expiration") != expiration_date.strftime("%y%m%d")
        or match.group("option_type") != option_type[0].upper()
        or encoded_strike != strike
    ):
        return None
    return normalized


def _datetime_field(payload: Mapping[str, object] | None, key: str) -> datetime | None:
    if payload is None:
        return None
    value = payload.get(key)
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _decimal_field(payload: Mapping[str, object] | None, key: str) -> Decimal | None:
    if payload is None:
        return None
    value = payload.get(key)
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite():
        return None
    return parsed if parsed >= 0 or key in {"delta", "theta", "vega", "rho"} else None


def _int_field(payload: Mapping[str, object] | None, key: str) -> int | None:
    if payload is None:
        return None
    value = payload.get(key)
    return value if isinstance(value, int) and value >= 0 else None
