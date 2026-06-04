from datetime import UTC, date, datetime, timedelta
import json

import pytest

from app.services import market_mood
from app.schemas.market_mood import MarketMoodDetailRead, MarketMoodRead
from app.services.market_mood import (
    DEFAULT_MARKET_MOOD_SNAPSHOT_PATH,
    CnnDerivedMarketMoodProvider,
    CnnFearGreedHttpClient,
    GLOBAL_MARKET_MOOD_STORE,
    MarketMoodRefreshError,
    MarketMoodService,
    MarketMoodSnapshotStore,
    SyntheticMarketMoodProvider,
    build_cnn_market_mood_refresh_runner,
    clear_active_market_mood_snapshot,
    load_market_mood_snapshot,
    read_from_snapshot,
    refresh_and_persist_market_mood_snapshot,
    save_market_mood_snapshot,
    unavailable_market_mood_read,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 6, 2, 15, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _clear_market_mood_snapshot():
    clear_active_market_mood_snapshot(disable_auto_restore=True)
    yield
    clear_active_market_mood_snapshot(disable_auto_restore=True)


def provider_payload() -> dict:
    return {
        "fear_and_greed": {
            "score": 62,
            "rating": "Greed",
            "updated_at": "2026-06-02T14:30:00Z",
            "raw_provider_url": "https://internal-provider.example.invalid/hidden",
        },
        "history": [
            {"date": "2026-05-26", "score": 58},
            {"date": "2025-06-02", "score": 40},
            {"date": "2026-06-02", "score": 62},
            {"date": "2026-05-02", "score": 50},
        ],
        "components": {
            "market_momentum": {
                "score": 66,
                "history": [
                    {"date": "2026-05-26", "value": 3.0, "score": 63},
                    {"date": "2026-06-02", "value": 3.4, "score": 66},
                ],
            },
            "stock_price_strength": {"score": 59},
            "stock_price_breadth": {"score": 55},
            "put_call_options": {
                "score": 42,
                "history": [
                    {"date": "2026-05-26", "value": 0.91, "score": 40},
                    {"date": "2026-06-02", "value": 0.88, "score": 42},
                ],
            },
            "market_volatility": {"score": 63},
            "safe_haven_demand": {"score": 38},
            "junk_bond_demand": {"score": 61},
        },
        "headers": {"cookie": "raw_cookie_should_not_persist"},
        "raw_payload": {"provider_id": "raw_should_not_persist"},
    }


def cnn_provider_payload() -> dict:
    return {
        "fear_and_greed": {
            "score": 64,
            "rating": "Greed",
            "timestamp": 1_780_389_000_000,
            "internal_url": "https://internal-provider.example.invalid/hidden",
        },
        "fear_and_greed_historical": {
            "data": [
                {"x": 1_746_141_200_000, "y": 42},
                {"x": 1_777_710_600_000, "y": 58},
                {"x": 1_780_389_000_000, "y": 64},
            ]
        },
        "market_momentum_sp500": {
            "score": 67,
            "data": [
                {"x": 1_777_710_600_000, "y": 2.8},
                {"x": 1_780_389_000_000, "y": 3.6},
            ],
        },
        "stock_price_strength": {"score": 61},
        "stock_price_breadth": {"score": 54},
        "put_call_options": {
            "score": 43,
            "data": [
                {"x": 1_777_710_600_000, "y": 0.91},
                {"x": 1_780_389_000_000, "y": 0.84},
            ],
        },
        "market_volatility_vix": {"score": 60},
        "safe_haven_demand": {"score": 39},
        "junk_bond_demand": {"score": 58},
        "headers": {"cookie": "raw_cookie_should_not_persist"},
        "raw_payload": {"provider_id": "raw_should_not_persist"},
    }


def test_synthetic_fixture_returns_safe_market_mood_contract() -> None:
    payload = MarketMoodService(SyntheticMarketMoodProvider(generated_at=NOW)).get_market_mood(current_time=NOW)

    assert payload.data_mode == "synthetic"
    assert payload.source_label == "CNN-derived Fear & Greed"
    assert payload.source_rights_notice == "Not affiliated with CNN. Internal demo only pending source/rights review."
    assert payload.is_trading_signal is False
    assert payload.is_actionability_input is False
    assert payload.is_risk_rule_input is False
    assert payload.score == 57.0
    assert payload.score_label == "57"
    assert payload.rating == "greed"
    assert len(payload.trend_series) == 4
    assert len(payload.components) == 7
    assert {component.component_key for component in payload.components} == {
        "market_momentum",
        "stock_price_strength",
        "stock_price_breadth",
        "put_call_options",
        "market_volatility",
        "safe_haven_demand",
        "junk_bond_demand",
    }
    assert {comparison.window for comparison in payload.comparisons} == {"1w", "1m", "1y"}
    assert all(comparison.is_available for comparison in payload.comparisons)
    assert not find_forbidden_keys(payload.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_runtime_default_returns_unavailable_without_provider_reference_last_good() -> None:
    compact = MarketMoodService().get_market_mood(current_time=NOW)
    detail = MarketMoodService().get_market_mood_detail(current_time=NOW)

    assert compact.data_mode == "unavailable"
    assert compact.score is None
    assert compact.components == ()
    assert detail.data_mode == "unavailable"
    assert detail.score is None
    assert detail.indicators == ()


def test_runtime_default_ignores_active_synthetic_fixture_snapshot() -> None:
    GLOBAL_MARKET_MOOD_STORE.activate(SyntheticMarketMoodProvider(generated_at=NOW).snapshot())

    compact = MarketMoodService().get_market_mood(current_time=NOW)
    detail = MarketMoodService().get_market_mood_detail(current_time=NOW)

    assert compact.data_mode == "unavailable"
    assert compact.score is None
    assert detail.data_mode == "unavailable"
    assert detail.indicators == ()


def test_provider_shaped_fixture_maps_current_score_trend_components_and_comparisons() -> None:
    class FakeClient:
        def fetch_market_mood(self):
            return provider_payload()

    snapshot = CnnDerivedMarketMoodProvider(FakeClient(), generated_at=NOW).snapshot()
    payload = read_from_snapshot(snapshot, current_time=NOW)
    rendered = repr(payload.model_dump(mode="python")).lower()

    assert payload.data_mode == "provider_reference"
    assert payload.source_detail_label == "Latest available snapshot"
    assert payload.updated_at_utc == datetime(2026, 6, 2, 14, 30, tzinfo=UTC)
    assert payload.updated_at_label == "2026-06-02T14:30:00Z"
    assert payload.freshness_status == "fresh"
    assert payload.score == 62.0
    assert payload.rating == "greed"
    assert [point.date for point in payload.trend_series] == [
        "2025-06-02",
        "2026-05-02",
        "2026-05-26",
        "2026-06-02",
    ]
    assert len(payload.components) == 7
    comparisons = {comparison.window: comparison for comparison in payload.comparisons}
    assert comparisons["1w"].prior_score == 58.0
    assert comparisons["1w"].change_label == "+4.0 points"
    assert comparisons["1m"].prior_score == 50.0
    assert comparisons["1y"].prior_score == 40.0
    assert "raw_provider_url" not in rendered
    assert "raw_payload" not in rendered
    assert "cookie" not in rendered
    assert "provider_id" not in rendered


def test_cnn_shaped_provider_payload_maps_aliases_without_raw_leakage() -> None:
    class FakeClient:
        def fetch_market_mood(self):
            return cnn_provider_payload()

    snapshot = CnnDerivedMarketMoodProvider(FakeClient(), generated_at=NOW).snapshot()
    compact = read_from_snapshot(snapshot, current_time=NOW)
    detail = MarketMoodService(provider=type("Provider", (), {"snapshot": lambda self: snapshot})()).get_market_mood_detail(
        current_time=NOW
    )
    indicators = {indicator.component_key: indicator for indicator in detail.indicators}
    rendered = repr(detail.model_dump(mode="python")).lower()

    assert compact.data_mode == "provider_reference"
    assert compact.score == 64.0
    assert len(compact.components) == 7
    assert indicators["market_momentum"].history
    assert indicators["market_momentum"].current_value_label == "3.6%"
    assert indicators["put_call_options"].history
    assert indicators["put_call_options"].current_value_label == "0.84"
    assert indicators["stock_price_strength"].history == ()
    assert "internal_url" not in rendered
    assert "raw_payload" not in rendered
    assert "cookie" not in rendered
    assert "provider_id" not in rendered


def test_runtime_default_returns_provider_reference_last_good_when_available() -> None:
    class FakeClient:
        def fetch_market_mood(self):
            return provider_payload()

    snapshot = CnnDerivedMarketMoodProvider(FakeClient(), generated_at=NOW).snapshot()
    GLOBAL_MARKET_MOOD_STORE.activate(snapshot)

    compact = MarketMoodService().get_market_mood(current_time=NOW)
    detail = MarketMoodService().get_market_mood_detail(current_time=NOW)

    assert compact.data_mode == "provider_reference"
    assert compact.score == 62.0
    assert len(compact.components) == 7
    assert detail.data_mode == "provider_reference"
    assert detail.score == 62.0
    assert len(detail.indicators) == 7


def test_synthetic_detail_contract_includes_all_indicator_histories_and_axis_metadata() -> None:
    snapshot = SyntheticMarketMoodProvider(generated_at=NOW).snapshot()
    payload = MarketMoodService(SyntheticMarketMoodProvider(generated_at=NOW)).get_market_mood_detail(current_time=NOW)

    assert payload.data_mode == "synthetic"
    assert payload.score == 57.0
    assert payload.trend_series
    assert len(payload.indicators) == 7
    assert {indicator.component_key for indicator in payload.indicators} == {
        "market_momentum",
        "stock_price_strength",
        "stock_price_breadth",
        "put_call_options",
        "market_volatility",
        "safe_haven_demand",
        "junk_bond_demand",
    }
    assert {indicator.axis_value_format for indicator in payload.indicators} >= {"percent", "ratio", "index", "spread"}
    for indicator in payload.indicators:
        assert indicator.subtitle
        assert indicator.description
        assert indicator.axis_label
        assert indicator.unit_label
        assert indicator.current_value is not None
        assert indicator.current_value_label
        assert indicator.current_score_label
        assert indicator.history
        assert all(point.value_label for point in indicator.history)
        assert all(point.score_label for point in indicator.history)
    assert snapshot.indicator_history


def test_provider_reference_detail_preserves_available_component_history_without_fabricating_missing_history() -> None:
    class FakeClient:
        def fetch_market_mood(self):
            return provider_payload()

    snapshot = CnnDerivedMarketMoodProvider(FakeClient(), generated_at=NOW).snapshot()
    payload = MarketMoodService(provider=type("Provider", (), {"snapshot": lambda self: snapshot})()).get_market_mood_detail(
        current_time=NOW
    )
    indicators = {indicator.component_key: indicator for indicator in payload.indicators}
    rendered = repr(payload.model_dump(mode="python")).lower()

    assert payload.data_mode == "provider_reference"
    assert indicators["market_momentum"].history
    assert indicators["market_momentum"].current_value_label == "3.4%"
    assert indicators["put_call_options"].history
    assert indicators["put_call_options"].current_value_label == "0.88"
    assert indicators["stock_price_strength"].history == ()
    assert indicators["stock_price_strength"].current_value is None
    assert "raw_provider_url" not in rendered
    assert "raw_payload" not in rendered
    assert "cookie" not in rendered


def test_stale_snapshot_is_explicitly_labelled() -> None:
    snapshot = SyntheticMarketMoodProvider(generated_at=NOW - timedelta(days=3)).snapshot()

    payload = read_from_snapshot(snapshot, current_time=NOW)

    assert payload.freshness_status == "stale"
    assert payload.freshness_label == "Latest available Market Mood snapshot is stale."


def test_unavailable_market_mood_read_is_safe() -> None:
    payload = unavailable_market_mood_read(current_time=NOW)

    assert payload.data_mode == "unavailable"
    assert payload.score is None
    assert payload.rating == "unknown"
    assert payload.trend_series == ()
    assert payload.components == ()
    assert all(comparison.is_available is False for comparison in payload.comparisons)
    assert payload.is_trading_signal is False
    assert payload.is_actionability_input is False
    assert payload.is_risk_rule_input is False


def test_malformed_provider_data_degrades_to_sanitized_failure() -> None:
    class MalformedClient:
        def fetch_market_mood(self):
            return {"raw_payload": {"headers": {"cookie": "secret_cookie"}}}

    with pytest.raises(MarketMoodRefreshError) as exc_info:
        CnnDerivedMarketMoodProvider(MalformedClient(), generated_at=NOW).snapshot()

    rendered = f"{str(exc_info.value)} {repr(exc_info.value.__cause__)} {repr(exc_info.value.__context__)}".lower()
    assert "raw_payload" not in rendered
    assert "cookie" not in rendered
    assert "secret_cookie" not in rendered


def test_http_client_uses_injected_transport_and_returns_json_mapping() -> None:
    seen_urls: list[str] = []

    def fake_fetch(url: str) -> str:
        seen_urls.append(url)
        return '{"fear_and_greed": {"score": 64}}'

    client = CnnFearGreedHttpClient(fetch_text=fake_fetch, endpoint_url="https://provider.example.invalid/private-path")

    payload = client.fetch_market_mood()

    assert payload == {"fear_and_greed": {"score": 64}}
    assert seen_urls == ["https://provider.example.invalid/private-path"]


def test_http_client_failure_strips_raw_url_payload_and_exception_chain() -> None:
    def leaking_fetch(_url: str) -> str:
        raise RuntimeError("raw_payload https://provider.example.invalid/private-path cookie provider_id")

    client = CnnFearGreedHttpClient(fetch_text=leaking_fetch, endpoint_url="https://provider.example.invalid/private-path")

    with pytest.raises(MarketMoodRefreshError) as exc_info:
        client.fetch_market_mood()

    rendered = f"{str(exc_info.value)} {repr(exc_info.value)} {repr(exc_info.value.__cause__)} {repr(exc_info.value.__context__)}".lower()
    assert "raw_payload" not in rendered
    assert "provider.example" not in rendered
    assert "cookie" not in rendered
    assert "provider_id" not in rendered


def test_http_client_default_transport_uses_dated_endpoint_and_browser_headers(monkeypatch) -> None:
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self) -> bytes:
            return b'{"fear_and_greed": {"score": 64}}'

    def fake_urlopen(request, timeout: int):
        seen["url"] = request.full_url
        seen["headers"] = {key.lower(): value for key, value in request.header_items()}
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(market_mood, "urlopen", fake_urlopen)

    payload = CnnFearGreedHttpClient().fetch_market_mood()

    assert payload == {"fear_and_greed": {"score": 64}}
    assert str(seen["url"]).endswith("/graphdata/2021-03-01")
    assert "mozilla/5.0" in str(seen["headers"]["user-agent"]).lower()
    assert seen["headers"]["referer"] == "https://www.cnn.com/markets/fear-and-greed"
    assert seen["timeout"] == 15


def test_cnn_refresh_runner_persists_and_activates_provider_reference_snapshot(tmp_path) -> None:
    path = tmp_path / "market_mood_snapshot.json"
    store = MarketMoodSnapshotStore()

    runner = build_cnn_market_mood_refresh_runner(
        fetch_text=lambda _url: json.dumps(cnn_provider_payload()),
        endpoint_url="https://provider.example.invalid/private-path",
        store=store,
        snapshot_path=path,
        now=lambda: NOW,
    )
    snapshot = runner()
    loaded = load_market_mood_snapshot(path=path)
    cache_text = path.read_text(encoding="utf-8").lower()

    assert snapshot.data_mode == "provider_reference"
    assert store.active_snapshot is snapshot
    assert loaded is not None
    assert read_from_snapshot(loaded, current_time=NOW).score == 64.0
    assert "provider.example" not in cache_text
    assert "raw_payload" not in cache_text
    assert "cookie" not in cache_text
    assert "provider_id" not in cache_text


def test_cnn_refresh_runner_failure_preserves_last_good_and_sanitizes(tmp_path) -> None:
    path = tmp_path / "market_mood_snapshot.json"
    store = MarketMoodSnapshotStore()
    last_good = CnnDerivedMarketMoodProvider(type("Client", (), {"fetch_market_mood": lambda self: provider_payload()})(), generated_at=NOW).snapshot()
    save_market_mood_snapshot(last_good, path=path)
    store.activate(last_good)

    runner = build_cnn_market_mood_refresh_runner(
        fetch_text=lambda _url: (_ for _ in ()).throw(RuntimeError("raw_payload https://provider.example.invalid cookie provider_id")),
        endpoint_url="https://provider.example.invalid/private-path",
        store=store,
        snapshot_path=path,
        now=lambda: NOW,
    )

    with pytest.raises(MarketMoodRefreshError) as exc_info:
        runner()

    loaded = load_market_mood_snapshot(path=path)
    rendered = f"{str(exc_info.value)} {repr(exc_info.value.__cause__)} {repr(exc_info.value.__context__)}".lower()
    assert store.active_snapshot is last_good
    assert loaded is not None
    assert read_from_snapshot(loaded, current_time=NOW).score == 62.0
    assert "raw_payload" not in rendered
    assert "provider.example" not in rendered
    assert "cookie" not in rendered
    assert "provider_id" not in rendered


def test_refresh_failure_preserves_active_and_persisted_last_good(tmp_path) -> None:
    class FailingProvider:
        def snapshot(self):
            raise RuntimeError("raw_payload https://internal.example.invalid cookie secret")

    path = tmp_path / "market_mood_snapshot.json"
    store = MarketMoodSnapshotStore()
    last_good = SyntheticMarketMoodProvider(generated_at=NOW).snapshot()
    save_market_mood_snapshot(last_good, path=path)
    store.activate(last_good)

    with pytest.raises(MarketMoodRefreshError) as exc_info:
        refresh_and_persist_market_mood_snapshot(provider=FailingProvider(), store=store, snapshot_path=path)

    assert store.active_snapshot is last_good
    loaded = load_market_mood_snapshot(path=path)
    assert loaded is not None
    assert loaded.generated_at == last_good.generated_at
    rendered = f"{str(exc_info.value)} {repr(exc_info.value.__cause__)} {repr(exc_info.value.__context__)}".lower()
    assert "raw_payload" not in rendered
    assert "internal.example" not in rendered
    assert "cookie" not in rendered
    assert "secret" not in rendered


def test_snapshot_cache_persists_only_normalized_json(tmp_path) -> None:
    class FakeClient:
        def fetch_market_mood(self):
            return provider_payload()

    path = tmp_path / "market_mood_snapshot.json"
    snapshot = CnnDerivedMarketMoodProvider(FakeClient(), generated_at=NOW).snapshot()

    save_market_mood_snapshot(snapshot, path=path)
    loaded = load_market_mood_snapshot(path=path)
    text = path.read_text(encoding="utf-8").lower()

    assert loaded is not None
    assert read_from_snapshot(loaded, current_time=NOW).score == 62.0
    assert "raw_provider_url" not in text
    assert "raw_payload" not in text
    assert "headers" not in text
    assert "cookie" not in text
    assert "provider_id" not in text
    assert DEFAULT_MARKET_MOOD_SNAPSHOT_PATH.parts[-3:] == ("backend", "cache", "market_mood_snapshot.json")


def test_market_mood_schema_rejects_invariant_flag_and_forbidden_wording() -> None:
    payload = SyntheticMarketMoodProvider(generated_at=NOW).snapshot()
    read = read_from_snapshot(payload, current_time=NOW).model_dump(mode="python")
    read["is_trading_signal"] = True

    with pytest.raises(ValueError):
        MarketMoodRead(**read)

    read = read_from_snapshot(payload, current_time=NOW).model_dump(mode="python")
    read["status_message"] = "safe to trade"

    with pytest.raises(ValueError):
        MarketMoodRead(**read)

    detail = MarketMoodService(SyntheticMarketMoodProvider(generated_at=NOW)).get_market_mood_detail(current_time=NOW).model_dump(
        mode="python"
    )
    detail["is_actionability_input"] = True

    with pytest.raises(ValueError):
        MarketMoodDetailRead(**detail)
