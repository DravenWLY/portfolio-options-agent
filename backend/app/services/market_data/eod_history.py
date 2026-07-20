"""FMP end-of-day history boundary and deterministic indicator snapshots.

This module is intentionally narrow:

- default runtime stays disabled/offline;
- live acquisition requires ``POA_MARKET_CONTEXT_MODE=live`` and ``FMP_API_KEY``;
- callers may inject fake clients for offline tests;
- raw provider payloads are normalized immediately and never returned.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import os
from typing import Any, Mapping, Protocol, Sequence
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import get_settings


FMP_EOD_HISTORY_URL = "https://financialmodelingprep.com/stable/historical-price-eod/full"
FMP_EOD_SOURCE_KEY = "fmp_eod_history"
FMP_EOD_SOURCE_LABEL = "FMP end-of-day data (internal evaluation use)"
FMP_EOD_CAVEAT_CODE = "eod_not_live_prices"
FMP_EOD_UNAVAILABLE_CAVEAT_CODE = "fmp_eod_history_not_available"
INSUFFICIENT_HISTORY_CAVEAT_CODE = "insufficient_history"
DEFAULT_EOD_HISTORY_LIMIT = 260
DEFAULT_MARKET_CONTEXT_MODE = "off"


class FmpEodHistoryError(RuntimeError):
    """Sanitized FMP EOD error that must not include URLs, keys, or payloads."""

    caveat_code = FMP_EOD_UNAVAILABLE_CAVEAT_CODE


class FmpEodHistoryRateLimitedError(FmpEodHistoryError):
    """The approved FMP lane rejected a request because its quota was exhausted."""

    caveat_code = "source_rate_limited"


class FmpEodHistorySubscriptionRequiredError(FmpEodHistoryError):
    """The configured FMP account does not include the approved EOD endpoint."""

    caveat_code = "source_subscription_required"


class FmpEodHistoryEndpointUnavailableError(FmpEodHistoryError):
    """The approved FMP endpoint was unavailable for the configured account."""

    caveat_code = "source_endpoint_not_available"


class FmpEodHistoryClient(Protocol):
    def fetch_eod_history(self, *, symbol: str, limit: int = DEFAULT_EOD_HISTORY_LIMIT) -> Sequence[Mapping[str, Any]]:
        """Return FMP-shaped EOD history rows through an injected boundary."""


@dataclass(frozen=True)
class EodBar:
    symbol: str
    bar_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int | None = None


@dataclass(frozen=True)
class FrozenEodHistoryWindow:
    """Normalized EOD rows retained only while one saved package is built."""

    symbol: str
    bars: tuple[EodBar, ...]
    collected_at: datetime
    freshness_category: str

    @property
    def first_date(self) -> date:
        return self.bars[0].bar_date

    @property
    def last_date(self) -> date:
        return self.bars[-1].bar_date


@dataclass(frozen=True)
class MarketContextPolicy:
    mode: str = DEFAULT_MARKET_CONTEXT_MODE
    request_timeout_seconds: int = 15
    response_size_cap_bytes: int = 512_000
    max_requests_per_run: int = 2

    @property
    def live_enabled(self) -> bool:
        return self.mode.strip().lower() == "live"


@dataclass
class MarketContextRequestBudget:
    max_requests: int = 2
    request_count: int = 0

    def consume(self) -> None:
        if self.request_count >= self.max_requests:
            raise FmpEodHistoryError("FMP EOD history request budget was exhausted")
        self.request_count += 1


@dataclass
class MarketContextExecutionContext:
    policy: MarketContextPolicy = field(default_factory=MarketContextPolicy)
    client: FmpEodHistoryClient | None = None
    budget: MarketContextRequestBudget = field(default_factory=MarketContextRequestBudget)
    cache: dict[str, "MarketContextSnapshot"] = field(default_factory=dict)
    history_cache: dict[str, FrozenEodHistoryWindow] = field(default_factory=dict)
    collected_at: datetime | None = None


@dataclass(frozen=True)
class MarketContextSnapshot:
    symbol: str
    as_of_date: date
    collected_at: datetime
    freshness_category: str
    row_count: int
    first_date: date
    last_date: date
    values: dict[str, float | int]
    indicators: dict[str, float]
    relationships: dict[str, str | float]
    omitted_indicators: tuple[str, ...]
    caveat_codes: tuple[str, ...]

    @property
    def as_of_datetime(self) -> datetime:
        return datetime.combine(self.as_of_date, time.min, tzinfo=UTC)

    def summary_payload(self) -> dict[str, object]:
        return {
            "source_key": FMP_EOD_SOURCE_KEY,
            "source_label": FMP_EOD_SOURCE_LABEL,
            "symbol": self.symbol,
            "as_of_date": self.as_of_date.isoformat(),
            "freshness_category": self.freshness_category,
            "data_window": {
                "row_count": self.row_count,
                "first_date": self.first_date.isoformat(),
                "last_date": self.last_date.isoformat(),
            },
            "values": self.values,
            "indicators": self.indicators,
            "relationships": self.relationships,
            "omitted_indicators": self.omitted_indicators,
        }


class FmpEodHistoryHttpClient:
    """Tiny runtime client used only behind explicit local/internal live mode."""

    def __init__(
        self,
        *,
        api_key: str,
        fetch_text: Any | None = None,
        endpoint_url: str = FMP_EOD_HISTORY_URL,
        timeout_seconds: int = 15,
        response_size_cap_bytes: int = 512_000,
    ) -> None:
        key = api_key.strip()
        if not key:
            raise FmpEodHistoryError("FMP EOD history is not configured")
        self._api_key = key
        self._fetch_text = fetch_text or self._fetch_public_text_url
        self._endpoint_url = endpoint_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._response_size_cap_bytes = response_size_cap_bytes

    def fetch_eod_history(self, *, symbol: str, limit: int = DEFAULT_EOD_HISTORY_LIMIT) -> Sequence[Mapping[str, Any]]:
        normalized_symbol = normalize_market_context_symbol(symbol)
        query = urlencode({"symbol": normalized_symbol, "apikey": self._api_key})
        url = f"{self._endpoint_url}?{query}"
        try:
            payload = json.loads(self._fetch_text(url))
        except HTTPError as exc:
            if exc.code == 429:
                raise FmpEodHistoryRateLimitedError("FMP EOD history rate limit was reached") from None
            if exc.code == 402:
                raise FmpEodHistorySubscriptionRequiredError(
                    "FMP EOD history requires source access not included in the configured account"
                ) from None
            if exc.code in {403, 404}:
                raise FmpEodHistoryEndpointUnavailableError(
                    "FMP EOD history endpoint was unavailable"
                ) from None
            raise FmpEodHistoryError("FMP EOD history fetch failed") from None
        except Exception:
            raise FmpEodHistoryError("FMP EOD history fetch failed") from None
        return _extract_fmp_eod_rows(payload)

    def _fetch_public_text_url(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": "portfolio-options-agent-market-context/0.1"})
        with urlopen(request, timeout=self._timeout_seconds) as response:  # nosec B310 - explicit opt-in public API fetch
            raw = response.read(self._response_size_cap_bytes + 1)
        if len(raw) > self._response_size_cap_bytes:
            raise FmpEodHistoryError("FMP EOD history response exceeded size cap")
        return raw.decode("utf-8", errors="replace")


def _extract_fmp_eod_rows(payload: object) -> tuple[Mapping[str, Any], ...]:
    rows = payload.get("historical") if isinstance(payload, Mapping) else payload
    if not isinstance(rows, list):
        raise FmpEodHistoryError("FMP EOD history response was unavailable")
    required_keys = frozenset({"date", "open", "high", "low", "close", "volume"})
    return tuple(row for row in rows if isinstance(row, Mapping) and required_keys.issubset(row.keys()))


def market_context_policy_from_environment(env: Mapping[str, str] | None = None) -> MarketContextPolicy:
    values = os.environ if env is None else env
    return MarketContextPolicy(mode=(values.get("POA_MARKET_CONTEXT_MODE") or DEFAULT_MARKET_CONTEXT_MODE).strip().lower())


def default_market_context_execution_context() -> MarketContextExecutionContext:
    policy = market_context_policy_from_environment()
    budget = MarketContextRequestBudget(max_requests=policy.max_requests_per_run)
    if not policy.live_enabled:
        return MarketContextExecutionContext(policy=policy, budget=budget)
    settings = get_settings()
    client = FmpEodHistoryHttpClient(
        api_key=settings.require_fmp_api_key(),
        timeout_seconds=policy.request_timeout_seconds,
        response_size_cap_bytes=policy.response_size_cap_bytes,
    )
    return MarketContextExecutionContext(policy=policy, client=client, budget=budget)


def market_context_execution_context_for_client(
    client: FmpEodHistoryClient | None,
    *,
    live_enabled: bool = True,
    max_requests_per_run: int = 2,
    collected_at: datetime | None = None,
) -> MarketContextExecutionContext:
    policy = MarketContextPolicy(
        mode="live" if live_enabled else "off",
        max_requests_per_run=max_requests_per_run,
    )
    return MarketContextExecutionContext(
        policy=policy,
        client=client,
        budget=MarketContextRequestBudget(max_requests=max_requests_per_run),
        collected_at=collected_at,
    )


def get_market_context_snapshot(
    *,
    symbol: str,
    context: MarketContextExecutionContext | None = None,
    limit: int = DEFAULT_EOD_HISTORY_LIMIT,
) -> MarketContextSnapshot:
    active_context = context or default_market_context_execution_context()
    normalized_symbol = normalize_market_context_symbol(symbol)
    cached = active_context.cache.get(normalized_symbol)
    if cached is not None:
        return cached
    window = get_frozen_eod_history_window(
        symbol=normalized_symbol,
        context=active_context,
        limit=limit,
    )
    snapshot = build_market_context_snapshot(
        normalized_symbol,
        window.bars,
        collected_at=window.collected_at,
    )
    active_context.cache[normalized_symbol] = snapshot
    return snapshot


def get_frozen_eod_history_window(
    *,
    symbol: str,
    context: MarketContextExecutionContext | None = None,
    limit: int = DEFAULT_EOD_HISTORY_LIMIT,
) -> FrozenEodHistoryWindow:
    """Fetch and normalize one bounded EOD window for generation-time freezing.

    Consumers receive normalized rows only.  The cache belongs to the injected
    package-build context, never to readback or to a cross-package raw cache.
    """

    active_context = context or default_market_context_execution_context()
    normalized_symbol = normalize_market_context_symbol(symbol)
    cached = active_context.history_cache.get(normalized_symbol)
    if cached is not None:
        return cached
    if not active_context.policy.live_enabled or active_context.client is None:
        raise FmpEodHistoryError("FMP EOD history source is disabled")
    active_context.budget.consume()
    try:
        rows = active_context.client.fetch_eod_history(symbol=normalized_symbol, limit=limit)
    except FmpEodHistoryError:
        raise
    except Exception:
        raise FmpEodHistoryError("FMP EOD history fetch failed") from None
    bars = normalize_eod_history_rows(rows, symbol=normalized_symbol)
    collected_at = active_context.collected_at or datetime.now(UTC)
    window = FrozenEodHistoryWindow(
        symbol=normalized_symbol,
        bars=bars,
        collected_at=collected_at,
        freshness_category=_freshness_category(bars[-1].bar_date, collected_at=collected_at),
    )
    active_context.history_cache[normalized_symbol] = window
    return window


def normalize_market_context_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized or not normalized.replace(".", "").replace("-", "").isalnum():
        raise FmpEodHistoryError("reviewed market-context symbol is unavailable")
    return normalized


def normalize_eod_history_rows(rows: Sequence[Mapping[str, Any]], *, symbol: str) -> tuple[EodBar, ...]:
    bars: list[EodBar] = []
    normalized_symbol = normalize_market_context_symbol(symbol)
    for row in rows:
        try:
            bar = EodBar(
                symbol=normalized_symbol,
                bar_date=_parse_date(row.get("date")),
                open=_decimal(row.get("open"), field_name="open"),
                high=_decimal(row.get("high"), field_name="high"),
                low=_decimal(row.get("low"), field_name="low"),
                close=_decimal(row.get("close"), field_name="close"),
                volume=_optional_int(row.get("volume")),
            )
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise FmpEodHistoryError("FMP EOD history rows were malformed") from exc
        if bar.low < 0 or bar.open < 0 or bar.high < 0 or bar.close < 0 or bar.high < bar.low:
            raise FmpEodHistoryError("FMP EOD history rows were malformed")
        bars.append(bar)
    deduped = {bar.bar_date: bar for bar in bars}
    ordered = tuple(deduped[bar_date] for bar_date in sorted(deduped))
    if len(ordered) < 2:
        raise FmpEodHistoryError("FMP EOD history had insufficient rows")
    return ordered[-DEFAULT_EOD_HISTORY_LIMIT:]


def build_market_context_snapshot(
    symbol: str,
    bars: Sequence[EodBar],
    *,
    collected_at: datetime,
) -> MarketContextSnapshot:
    if len(bars) < 2:
        raise FmpEodHistoryError("FMP EOD history had insufficient rows")
    ordered = tuple(sorted(bars, key=lambda bar: bar.bar_date))[-DEFAULT_EOD_HISTORY_LIMIT:]
    closes = tuple(bar.close for bar in ordered)
    latest = ordered[-1]
    prior = ordered[-2]
    values: dict[str, float | int] = {
        "latest_close": _round_float(latest.close),
        "prior_close": _round_float(prior.close),
    }
    if latest.volume is not None:
        values["latest_volume"] = latest.volume
    indicators: dict[str, float] = {}
    relationships: dict[str, str | float] = {}
    omitted: list[str] = []

    _put_indicator(indicators, omitted, "sma50", _sma(closes, 50))
    _put_indicator(indicators, omitted, "sma200", _sma(closes, 200))
    _put_indicator(indicators, omitted, "ema10", _ema_latest(closes, 10))
    _put_indicator(indicators, omitted, "rsi14", _rsi_latest(closes, 14))
    macd = _macd_latest(closes)
    if macd is None:
        omitted.extend(("macd", "macd_signal", "macd_histogram"))
    else:
        indicators.update({key: _round_float(value) for key, value in macd.items()})
    bollinger = _bollinger_latest(closes, 20)
    if bollinger is None:
        omitted.extend(("bollinger_middle", "bollinger_upper", "bollinger_lower"))
    else:
        indicators.update({key: _round_float(value) for key, value in bollinger.items()})
    _put_indicator(indicators, omitted, "atr14", _atr_latest(ordered, 14))

    high_low = _fifty_two_week_high_low(ordered)
    if high_low is None:
        omitted.extend(("high_52_week", "low_52_week"))
    else:
        values["high_52_week"] = _round_float(high_low[0])
        values["low_52_week"] = _round_float(high_low[1])

    for key in ("sma50", "sma200"):
        average = indicators.get(key)
        if average is None:
            continue
        relationships[f"close_vs_{key}"] = _close_relationship(values["latest_close"], average)
        relationships[f"distance_to_{key}_percent"] = _round_float(
            (Decimal(str(values["latest_close"])) - Decimal(str(average))) / Decimal(str(average)) * Decimal("100")
        )

    caveats = [FMP_EOD_CAVEAT_CODE]
    if omitted:
        caveats.append(INSUFFICIENT_HISTORY_CAVEAT_CODE)
    return MarketContextSnapshot(
        symbol=normalize_market_context_symbol(symbol),
        as_of_date=latest.bar_date,
        collected_at=collected_at,
        freshness_category=_freshness_category(latest.bar_date, collected_at=collected_at),
        row_count=len(ordered),
        first_date=ordered[0].bar_date,
        last_date=latest.bar_date,
        values=values,
        indicators=indicators,
        relationships=relationships,
        omitted_indicators=tuple(dict.fromkeys(omitted)),
        caveat_codes=tuple(caveats),
    )


def _put_indicator(indicators: dict[str, float], omitted: list[str], key: str, value: Decimal | None) -> None:
    if value is None:
        omitted.append(key)
        return
    indicators[key] = _round_float(value)


def _sma(values: Sequence[Decimal], period: int) -> Decimal | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / Decimal(period)


def _ema_series(values: Sequence[Decimal], period: int) -> tuple[Decimal | None, ...]:
    if len(values) < period:
        return tuple(None for _ in values)
    seed = sum(values[:period]) / Decimal(period)
    multiplier = Decimal("2") / Decimal(period + 1)
    output: list[Decimal | None] = [None] * (period - 1)
    ema = seed
    output.append(ema)
    for value in values[period:]:
        ema = (value - ema) * multiplier + ema
        output.append(ema)
    return tuple(output)


def _ema_latest(values: Sequence[Decimal], period: int) -> Decimal | None:
    series = _ema_series(values, period)
    return series[-1] if series and series[-1] is not None else None


def _rsi_latest(values: Sequence[Decimal], period: int) -> Decimal | None:
    if len(values) < period + 1:
        return None
    changes = [values[index] - values[index - 1] for index in range(1, len(values))]
    gains = [max(change, Decimal("0")) for change in changes]
    losses = [abs(min(change, Decimal("0"))) for change in changes]
    avg_gain = sum(gains[:period]) / Decimal(period)
    avg_loss = sum(losses[:period]) / Decimal(period)
    for index in range(period, len(changes)):
        avg_gain = ((avg_gain * Decimal(period - 1)) + gains[index]) / Decimal(period)
        avg_loss = ((avg_loss * Decimal(period - 1)) + losses[index]) / Decimal(period)
    if avg_loss == 0:
        return Decimal("100")
    if avg_gain == 0:
        return Decimal("0")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def _macd_latest(values: Sequence[Decimal]) -> dict[str, Decimal] | None:
    ema12 = _ema_series(values, 12)
    ema26 = _ema_series(values, 26)
    macd_values: list[Decimal] = []
    for fast, slow in zip(ema12, ema26, strict=True):
        if fast is None or slow is None:
            continue
        macd_values.append(fast - slow)
    signal = _ema_latest(macd_values, 9)
    if not macd_values or signal is None:
        return None
    macd = macd_values[-1]
    return {
        "macd": macd,
        "macd_signal": signal,
        "macd_histogram": macd - signal,
    }


def _bollinger_latest(values: Sequence[Decimal], period: int) -> dict[str, Decimal] | None:
    if len(values) < period:
        return None
    window = values[-period:]
    middle = sum(window) / Decimal(period)
    variance = sum((value - middle) ** 2 for value in window) / Decimal(period)
    stddev = Decimal(str(float(variance) ** 0.5))
    return {
        "bollinger_middle": middle,
        "bollinger_upper": middle + (stddev * Decimal("2")),
        "bollinger_lower": middle - (stddev * Decimal("2")),
    }


def _atr_latest(bars: Sequence[EodBar], period: int) -> Decimal | None:
    if len(bars) < period + 1:
        return None
    ranges: list[Decimal] = []
    for index in range(1, len(bars)):
        current = bars[index]
        previous = bars[index - 1]
        ranges.append(max(current.high - current.low, abs(current.high - previous.close), abs(current.low - previous.close)))
    return sum(ranges[-period:]) / Decimal(period)


def _fifty_two_week_high_low(bars: Sequence[EodBar]) -> tuple[Decimal, Decimal] | None:
    if len(bars) < 252:
        return None
    window = bars[-252:]
    return max(bar.high for bar in window), min(bar.low for bar in window)


def _close_relationship(close: float | int, indicator: float) -> str:
    close_decimal = Decimal(str(close))
    indicator_decimal = Decimal(str(indicator))
    if close_decimal > indicator_decimal:
        return "above"
    if close_decimal < indicator_decimal:
        return "below"
    return "equal"


def _freshness_category(as_of_date: date, *, collected_at: datetime) -> str:
    age_days = max(0, (collected_at.date() - as_of_date).days)
    if age_days <= 3:
        return "fresh"
    if age_days <= 10:
        return "stale"
    return "unknown"


def _round_float(value: Decimal | float | int, places: int = 6) -> float:
    decimal = Decimal(str(value)).quantize(Decimal("1." + ("0" * places)), rounding=ROUND_HALF_UP)
    return float(decimal)


def _parse_date(value: object) -> date:
    if not isinstance(value, str):
        raise ValueError("date is required")
    return date.fromisoformat(value)


def _decimal(value: object, *, field_name: str) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} is required")
    return Decimal(str(value))


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)
