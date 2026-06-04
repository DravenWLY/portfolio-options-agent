from datetime import UTC, datetime
import json

import pytest
from fastapi.testclient import TestClient

from app.api.routes.market_context import get_market_mood_refresh_runner
from app.services.market_mood import (
    CnnDerivedMarketMoodProvider,
    GLOBAL_MARKET_MOOD_STORE,
    MarketMoodRefreshError,
    build_cnn_market_mood_refresh_runner,
    clear_active_market_mood_snapshot,
    load_market_mood_snapshot,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


pytestmark = [pytest.mark.api, pytest.mark.unit]

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


def activate_provider_reference_snapshot() -> None:
    class FakeClient:
        def fetch_market_mood(self):
            return provider_payload()

    GLOBAL_MARKET_MOOD_STORE.activate(CnnDerivedMarketMoodProvider(FakeClient(), generated_at=NOW).snapshot())


def test_market_mood_route_returns_provider_neutral_shape(client: TestClient) -> None:
    response = client.get("/market-context/market-mood")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "data_mode",
        "source_label",
        "source_detail_label",
        "source_rights_notice",
        "generated_at",
        "updated_at_utc",
        "updated_at_label",
        "freshness_status",
        "freshness_label",
        "is_trading_signal",
        "is_actionability_input",
        "is_risk_rule_input",
        "score",
        "score_label",
        "score_min",
        "score_max",
        "rating",
        "rating_label",
        "trend_series",
        "comparisons",
        "components",
        "caveat_codes",
        "limitations",
        "status_message",
    }
    assert payload["data_mode"] == "unavailable"
    assert payload["source_label"] == "Market Mood unavailable"
    assert payload["source_rights_notice"] == "Not affiliated with CNN. Internal demo only pending source/rights review."
    assert payload["is_trading_signal"] is False
    assert payload["is_actionability_input"] is False
    assert payload["is_risk_rule_input"] is False
    assert payload["score"] is None
    assert payload["components"] == []
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_market_mood_route_returns_provider_reference_last_good(client: TestClient) -> None:
    activate_provider_reference_snapshot()

    response = client.get("/market-context/market-mood")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    assert payload["data_mode"] == "provider_reference"
    assert payload["source_label"] == "CNN-derived Fear & Greed"
    assert payload["score"] == 62.0
    assert len(payload["components"]) == 7
    assert "raw_provider_url" not in rendered
    assert "raw_payload" not in rendered
    assert "cookie" not in rendered
    assert "provider_id" not in rendered


def test_market_mood_detail_route_returns_full_indicator_contract(client: TestClient) -> None:
    response = client.get("/market-context/market-mood/detail")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "data_mode",
        "source_label",
        "source_detail_label",
        "source_rights_notice",
        "generated_at",
        "updated_at_utc",
        "updated_at_label",
        "freshness_status",
        "freshness_label",
        "is_trading_signal",
        "is_actionability_input",
        "is_risk_rule_input",
        "score",
        "score_label",
        "score_min",
        "score_max",
        "rating",
        "rating_label",
        "trend_series",
        "comparisons",
        "indicators",
        "caveat_codes",
        "limitations",
        "status_message",
    }
    assert payload["data_mode"] == "unavailable"
    assert payload["is_trading_signal"] is False
    assert payload["is_actionability_input"] is False
    assert payload["is_risk_rule_input"] is False
    assert payload["score"] is None
    assert payload["indicators"] == []
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_market_mood_detail_route_returns_provider_reference_without_fabricating_missing_history(client: TestClient) -> None:
    activate_provider_reference_snapshot()

    response = client.get("/market-context/market-mood/detail")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    assert payload["data_mode"] == "provider_reference"
    assert payload["score"] == 62.0
    assert len(payload["indicators"]) == 7
    indicators = {indicator["component_key"]: indicator for indicator in payload["indicators"]}
    assert indicators["market_momentum"]["history"]
    assert indicators["market_momentum"]["current_value_label"] == "3.4%"
    assert indicators["put_call_options"]["history"]
    assert indicators["put_call_options"]["current_value_label"] == "0.88"
    assert indicators["stock_price_strength"]["history"] == []
    assert indicators["stock_price_strength"]["current_value"] is None
    for indicator in payload["indicators"]:
        assert set(indicator) == {
            "component_key",
            "display_name",
            "subtitle",
            "description",
            "current_score",
            "current_score_label",
            "current_rating",
            "current_rating_label",
            "current_value",
            "current_value_label",
            "unit_label",
            "axis_label",
            "axis_value_format",
            "higher_value_meaning",
            "lower_value_meaning",
            "history",
        }
        assert indicator["subtitle"]
        assert indicator["description"]
        assert all(point["value_label"] for point in indicator["history"])
        assert all(point["score_label"] for point in indicator["history"])
    assert "raw_provider_url" not in rendered
    assert "raw_payload" not in rendered
    assert "cookie" not in rendered
    assert "provider_id" not in rendered
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_market_mood_refresh_route_returns_sanitized_provider_reference_success(app, client: TestClient, tmp_path) -> None:
    path = tmp_path / "market_mood_snapshot.json"
    runner = build_cnn_market_mood_refresh_runner(
        fetch_text=lambda _url: json.dumps(provider_payload()),
        endpoint_url="https://provider.example.invalid/private-path",
        snapshot_path=path,
        now=lambda: NOW,
    )

    app.dependency_overrides[get_market_mood_refresh_runner] = lambda: runner
    try:
        response = client.post("/market-context/market-mood/refresh")
    finally:
        app.dependency_overrides.pop(get_market_mood_refresh_runner, None)

    assert response.status_code == 200
    payload = response.json()
    loaded = load_market_mood_snapshot(path=path)
    assert payload["status"] == "refreshed"
    assert payload["data_mode"] == "provider_reference"
    assert payload["source_label"] == "CNN-derived Fear & Greed"
    assert payload["record_count"] == 4
    assert payload["message"] == "Market Mood refresh completed."
    assert loaded is not None
    assert client.get("/market-context/market-mood").json()["data_mode"] == "provider_reference"
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_market_mood_refresh_route_returns_sanitized_failure(app, client: TestClient) -> None:
    def runner():
        raise MarketMoodRefreshError("raw_payload https://internal.example.invalid cookie provider_id")

    app.dependency_overrides[get_market_mood_refresh_runner] = lambda: runner
    try:
        response = client.post("/market-context/market-mood/refresh")
    finally:
        app.dependency_overrides.pop(get_market_mood_refresh_runner, None)

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    assert payload["status"] == "failed"
    assert payload["data_mode"] == "unavailable"
    assert payload["record_count"] == 0
    assert payload["message"] == "Market Mood refresh failed; last good snapshot was preserved."
    assert "raw_payload" not in rendered
    assert "internal.example" not in rendered
    assert "cookie" not in rendered
    assert "provider_id" not in rendered


def test_market_mood_refresh_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.post("/market-context/market-mood/refresh")

    assert response.status_code == 401


def test_market_context_routes_avoid_forbidden_wording(app, client: TestClient) -> None:
    def runner():
        raise MarketMoodRefreshError("raw_payload https://internal.example.invalid cookie provider_id")

    app.dependency_overrides[get_market_mood_refresh_runner] = lambda: runner
    mood_payload = client.get("/market-context/market-mood").json()
    detail_payload = client.get("/market-context/market-mood/detail").json()
    try:
        refresh_payload = client.post("/market-context/market-mood/refresh").json()
    finally:
        app.dependency_overrides.pop(get_market_mood_refresh_runner, None)
    rendered = repr((mood_payload, detail_payload, refresh_payload)).lower()
    forbidden_text = (
        "raw_provider_payload",
        "raw_payload",
        "provider_account_id",
        "account_id",
        "threshold",
        "prompt",
        "llm_response",
        "safe to trade",
        "ready to trade",
        "guaranteed return",
        "place order",
        "execute trade",
        "buy ",
        "sell ",
        "risk-on",
        "risk-off",
        "recommendation",
    )

    assert not find_forbidden_keys(mood_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(detail_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(refresh_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not any(text in rendered for text in forbidden_text)
