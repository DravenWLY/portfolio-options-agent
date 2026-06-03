from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.routes.market_context import get_market_mood_refresh_runner
from app.services.market_mood import (
    MarketMoodRefreshError,
    SyntheticMarketMoodProvider,
    clear_active_market_mood_snapshot,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


pytestmark = [pytest.mark.api, pytest.mark.unit]

NOW = datetime(2026, 6, 2, 15, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _clear_market_mood_snapshot():
    clear_active_market_mood_snapshot(disable_auto_restore=True)
    yield
    clear_active_market_mood_snapshot(disable_auto_restore=True)


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
    assert payload["data_mode"] == "synthetic"
    assert payload["source_label"] == "CNN-derived Fear & Greed"
    assert payload["source_rights_notice"] == "Not affiliated with CNN. Internal demo only pending source/rights review."
    assert payload["is_trading_signal"] is False
    assert payload["is_actionability_input"] is False
    assert payload["is_risk_rule_input"] is False
    assert len(payload["components"]) == 7
    assert set(payload["components"][0]) == {
        "component_key",
        "display_name",
        "score",
        "score_label",
        "rating",
        "rating_label",
    }
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_market_mood_refresh_route_returns_sanitized_success(app, client: TestClient) -> None:
    snapshot = SyntheticMarketMoodProvider(generated_at=NOW).snapshot()

    def runner():
        return snapshot

    app.dependency_overrides[get_market_mood_refresh_runner] = lambda: runner
    try:
        response = client.post("/market-context/market-mood/refresh")
    finally:
        app.dependency_overrides.pop(get_market_mood_refresh_runner, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refreshed"
    assert payload["data_mode"] == "synthetic"
    assert payload["source_label"] == "CNN-derived Fear & Greed"
    assert payload["record_count"] == len(snapshot.trend_series)
    assert payload["message"] == "Market Mood refresh completed."
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


def test_market_context_routes_avoid_forbidden_wording(client: TestClient) -> None:
    mood_payload = client.get("/market-context/market-mood").json()
    refresh_payload = client.post("/market-context/market-mood/refresh").json()
    rendered = repr((mood_payload, refresh_payload)).lower()
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
    assert not find_forbidden_keys(refresh_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not any(text in rendered for text in forbidden_text)
