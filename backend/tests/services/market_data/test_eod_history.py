from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import json
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlparse

import pytest

from app.services.market_data.eod_history import (
    FMP_EOD_HISTORY_URL,
    FmpEodHistoryEndpointUnavailableError,
    FmpEodHistoryHttpClient,
    FmpEodHistoryError,
    FmpEodHistoryRateLimitedError,
    FmpEodHistorySubscriptionRequiredError,
    build_market_context_snapshot,
    market_context_execution_context_for_client,
    normalize_eod_history_rows,
    get_market_context_snapshot,
)


pytestmark = [pytest.mark.unit]


class _FakeFmpEodClient:
    def __init__(self, rows):
        self.rows = tuple(rows)
        self.calls: list[tuple[str, int]] = []

    def fetch_eod_history(self, *, symbol: str, limit: int = 260):
        self.calls.append((symbol, limit))
        return self.rows


def test_eod_history_indicators_match_hand_checked_golden_values() -> None:
    rows = _linear_rows(260)
    bars = normalize_eod_history_rows(rows, symbol="xyz")

    snapshot = build_market_context_snapshot(
        "XYZ",
        bars,
        collected_at=datetime.combine(bars[-1].bar_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC),
    )

    assert snapshot.symbol == "XYZ"
    assert snapshot.row_count == 260
    assert snapshot.values["latest_close"] == 260.0
    assert snapshot.values["prior_close"] == 259.0
    assert snapshot.values["latest_volume"] == 1260
    assert snapshot.values["high_52_week"] == 261.0
    assert snapshot.values["low_52_week"] == 8.0
    assert snapshot.indicators["sma50"] == 235.5
    assert snapshot.indicators["sma200"] == 160.5
    assert snapshot.indicators["ema10"] == 255.5
    assert snapshot.indicators["rsi14"] == 100.0
    assert snapshot.indicators["macd"] == 7.0
    assert snapshot.indicators["macd_signal"] == 7.0
    assert snapshot.indicators["macd_histogram"] == 0.0
    assert snapshot.indicators["bollinger_middle"] == 250.5
    assert snapshot.indicators["bollinger_upper"] == 262.032563
    assert snapshot.indicators["bollinger_lower"] == 238.967437
    assert snapshot.indicators["atr14"] == 2.0
    assert snapshot.relationships["close_vs_sma50"] == "above"
    assert snapshot.relationships["close_vs_sma200"] == "above"
    assert snapshot.relationships["distance_to_sma50_percent"] == 10.403397
    assert snapshot.relationships["distance_to_sma200_percent"] == 61.993769
    assert snapshot.caveat_codes == ("eod_not_live_prices",)


def test_eod_history_short_history_omits_indicators_with_caveat() -> None:
    rows = _linear_rows(20)
    bars = normalize_eod_history_rows(rows, symbol="XYZ")

    snapshot = build_market_context_snapshot(
        "XYZ",
        bars,
        collected_at=datetime.combine(bars[-1].bar_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC),
    )

    assert snapshot.values["latest_close"] == 20.0
    assert "sma50" not in snapshot.indicators
    assert "sma200" not in snapshot.indicators
    assert "high_52_week" not in snapshot.values
    assert "insufficient_history" in snapshot.caveat_codes
    assert {"sma50", "sma200", "high_52_week", "low_52_week"}.issubset(set(snapshot.omitted_indicators))


def test_eod_history_context_enforces_shared_budget_and_cache() -> None:
    client = _FakeFmpEodClient(_linear_rows(260))
    context = market_context_execution_context_for_client(
        client,
        collected_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    first = get_market_context_snapshot(symbol="XYZ", context=context)
    second = get_market_context_snapshot(symbol="xyz", context=context)

    assert first is second
    assert client.calls == [("XYZ", 260)]

    get_market_context_snapshot(symbol="ABC", context=context)
    with pytest.raises(FmpEodHistoryError, match="budget"):
        get_market_context_snapshot(symbol="DEF", context=context)


def test_eod_history_disabled_context_makes_no_client_call() -> None:
    client = _FakeFmpEodClient(_linear_rows(260))
    context = market_context_execution_context_for_client(client, live_enabled=False)

    with pytest.raises(FmpEodHistoryError, match="disabled"):
        get_market_context_snapshot(symbol="XYZ", context=context)

    assert client.calls == []


def test_eod_history_malformed_rows_fail_closed() -> None:
    rows = [{"date": "2026-01-01", "open": "1", "high": "2", "low": "1"}]

    with pytest.raises(FmpEodHistoryError, match="malformed"):
        normalize_eod_history_rows(rows, symbol="XYZ")


def test_fmp_eod_http_client_uses_stable_endpoint_with_symbol_query_param() -> None:
    captured_urls: list[str] = []

    def fake_fetch_text(url: str) -> str:
        captured_urls.append(url)
        return json.dumps(_linear_rows(3))

    client = FmpEodHistoryHttpClient(
        api_key="synthetic-test-key",
        fetch_text=fake_fetch_text,
    )

    rows = client.fetch_eod_history(symbol="xyz")

    assert len(rows) == 3
    assert len(captured_urls) == 1
    parsed = urlparse(captured_urls[0])
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == FMP_EOD_HISTORY_URL
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    assert {name for name, _value in query_pairs} == {"symbol", "apikey"}
    assert [value for name, value in query_pairs if name == "symbol"] == ["XYZ"]


def test_fmp_eod_http_client_accepts_stable_array_response_shape() -> None:
    rows = _linear_rows(3)
    client = FmpEodHistoryHttpClient(
        api_key="synthetic-test-key",
        fetch_text=lambda _url: json.dumps([rows[0], {"date": "2026-01-01"}, rows[1], rows[2]]),
    )

    parsed_rows = client.fetch_eod_history(symbol="XYZ")

    assert parsed_rows == rows


def test_fmp_eod_http_client_accepts_legacy_historical_wrapper() -> None:
    rows = _linear_rows(3)
    client = FmpEodHistoryHttpClient(
        api_key="synthetic-test-key",
        fetch_text=lambda _url: json.dumps({"historical": rows}),
    )

    parsed_rows = client.fetch_eod_history(symbol="XYZ")

    assert parsed_rows == rows


def test_fmp_eod_http_client_rejects_unavailable_response_shape_safely() -> None:
    client = FmpEodHistoryHttpClient(
        api_key="synthetic-test-key",
        fetch_text=lambda _url: json.dumps({"unexpected": []}),
    )

    with pytest.raises(FmpEodHistoryError, match="response was unavailable") as exc_info:
        client.fetch_eod_history(symbol="XYZ")

    rendered_error = str(exc_info.value).lower()
    assert "http" not in rendered_error
    assert "synthetic-test-key" not in rendered_error
    assert "unexpected" not in rendered_error


@pytest.mark.parametrize(
    ("status_code", "error_type", "caveat_code"),
    (
        (429, FmpEodHistoryRateLimitedError, "source_rate_limited"),
        (402, FmpEodHistorySubscriptionRequiredError, "source_subscription_required"),
        (403, FmpEodHistoryEndpointUnavailableError, "source_endpoint_not_available"),
    ),
)
def test_fmp_eod_http_client_preserves_safe_http_failure_category(
    status_code: int,
    error_type: type[FmpEodHistoryError],
    caveat_code: str,
) -> None:
    def _raise_http_error(_url: str) -> str:
        raise HTTPError("https://example.invalid", status_code, "provider error", None, None)

    client = FmpEodHistoryHttpClient(
        api_key="synthetic-test-key",
        fetch_text=_raise_http_error,
    )

    with pytest.raises(error_type) as exc_info:
        client.fetch_eod_history(symbol="XYZ")

    assert exc_info.value.caveat_code == caveat_code
    assert "example.invalid" not in str(exc_info.value)
    assert "synthetic-test-key" not in str(exc_info.value)


def _linear_rows(count: int):
    start = date(2025, 1, 1)
    rows = []
    for index in range(count):
        close = Decimal(index + 1)
        rows.append(
            {
                "date": (start + timedelta(days=index)).isoformat(),
                "open": str(close),
                "high": str(close + Decimal("1")),
                "low": str(close - Decimal("1")),
                "close": str(close),
                "volume": 1001 + index,
            }
        )
    return tuple(reversed(rows))
