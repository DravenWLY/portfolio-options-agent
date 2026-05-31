from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.routes.economic_calendar import get_economic_calendar_current_date, get_economic_calendar_refresh_runner
from app.services.economic_calendar import EconomicCalendarRefreshError, FmpEconomicCalendarHttpClient, SyntheticEconomicCalendarProvider
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


pytestmark = [pytest.mark.api, pytest.mark.unit]


@pytest.fixture(autouse=True)
def _clear_fmp_api_key(monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)


def test_economic_calendar_events_route_returns_provider_neutral_shape(client: TestClient) -> None:
    response = client.get(
        "/economic-calendar/events",
        params={"start_date": "2026-05-29", "end_date": "2026-05-29"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "data_mode",
        "source_label",
        "as_of_label",
        "freshness_label",
        "window_start",
        "window_end",
        "timezone",
        "importance_source",
        "items",
        "demo_notice",
        "is_trading_signal",
        "limitations",
    }
    assert payload["data_mode"] == "synthetic"
    assert payload["source_label"] == "Synthetic economic calendar fixture"
    assert payload["is_trading_signal"] is False
    assert payload["items"]
    assert all(item["is_trading_signal"] is False for item in payload["items"])
    assert set(payload["items"][0]) == {
        "event_reference",
        "event_datetime_utc",
        "event_has_occurred",
        "event_date_label",
        "event_time_label",
        "event_title",
        "event_type",
        "importance",
        "importance_source",
        "country",
        "currency",
        "actual_label",
        "forecast_label",
        "previous_label",
        "unit_label",
        "source_label",
        "freshness_label",
        "is_trading_signal",
        "data_mode",
    }
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_economic_calendar_events_route_defaults_to_current_app_date(app, client: TestClient) -> None:
    app.dependency_overrides[get_economic_calendar_current_date] = lambda: date(2026, 6, 2)
    try:
        response = client.get("/economic-calendar/events")
    finally:
        app.dependency_overrides.pop(get_economic_calendar_current_date, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["window_start"] == "2026-06-02"
    assert payload["window_end"] == "2026-06-02"
    assert [item["event_date_label"] for item in payload["items"]] == ["2026-06-02"]


def test_economic_calendar_events_route_accepts_valid_one_day_and_multi_day_windows(client: TestClient) -> None:
    one_day = client.get("/economic-calendar/events", params={"start_date": "2026-05-29", "end_date": "2026-05-29"})
    seven_day = client.get("/economic-calendar/events", params={"start_date": "2026-05-29", "end_date": "2026-06-04"})
    # The former 7-day cap is removed: a wider window is now accepted (backend
    # filters the active snapshot to the requested range).
    wide = client.get("/economic-calendar/events", params={"start_date": "2026-05-29", "end_date": "2026-07-15"})

    assert one_day.status_code == 200
    assert one_day.json()["window_start"] == "2026-05-29"
    assert one_day.json()["window_end"] == "2026-05-29"
    assert {item["event_date_label"] for item in one_day.json()["items"]} == {"2026-05-29"}
    assert seven_day.status_code == 200
    assert seven_day.json()["window_start"] == "2026-05-29"
    assert seven_day.json()["window_end"] == "2026-06-04"
    assert wide.status_code == 200
    assert wide.json()["window_start"] == "2026-05-29"
    assert wide.json()["window_end"] == "2026-07-15"


@pytest.mark.parametrize(
    "params",
    (
        {"start_date": "05/29/2026"},
        {"start_date": "2026-05-30", "end_date": "2026-05-29"},
    ),
)
def test_economic_calendar_events_route_rejects_invalid_windows(client: TestClient, params: dict[str, str]) -> None:
    response = client.get("/economic-calendar/events", params=params)

    assert response.status_code == 400
    rendered = repr(response.json()).lower()
    assert "api_key" not in rendered
    assert "raw_payload" not in rendered


def test_economic_calendar_events_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.get("/economic-calendar/events")

    assert response.status_code == 401


def test_economic_calendar_refresh_route_returns_sanitized_success(app, client: TestClient) -> None:
    snapshot = SyntheticEconomicCalendarProvider().snapshot()

    def runner():
        return snapshot

    app.dependency_overrides[get_economic_calendar_refresh_runner] = lambda: runner
    try:
        response = client.post("/economic-calendar/refresh")
    finally:
        app.dependency_overrides.pop(get_economic_calendar_refresh_runner, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refreshed"
    assert payload["data_mode"] == "synthetic"
    assert payload["source_label"] == "Synthetic economic calendar fixture"
    assert payload["record_count"] == len(snapshot.records)
    assert payload["imported_at"] == datetime(2026, 5, 29, 13, 0, tzinfo=UTC).isoformat().replace("+00:00", "Z")
    assert payload["message"] == "Economic calendar refresh completed."
    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_economic_calendar_refresh_route_returns_sanitized_failure(app, client: TestClient) -> None:
    def runner():
        raise EconomicCalendarRefreshError("raw_payload api_key provider_account_id")

    app.dependency_overrides[get_economic_calendar_refresh_runner] = lambda: runner
    try:
        response = client.post("/economic-calendar/refresh")
    finally:
        app.dependency_overrides.pop(get_economic_calendar_refresh_runner, None)

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    assert payload["status"] == "failed"
    assert payload["data_mode"] == "unavailable"
    assert payload["record_count"] == 0
    assert payload["message"] == "Economic calendar refresh failed; last good snapshot was preserved."
    assert "raw_payload" not in rendered
    assert "api_key" not in rendered
    assert "provider_account_id" not in rendered


def test_economic_calendar_refresh_route_uses_fmp_when_key_present(app, client: TestClient, monkeypatch, tmp_path) -> None:
    from app.services import economic_calendar

    monkeypatch.setenv("FMP_API_KEY", "test_fmp_key")
    monkeypatch.setattr(economic_calendar, "DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH", tmp_path / "calendar.json")
    captured_urls = []

    def fake_fetch(self, url: str) -> str:
        captured_urls.append(url)
        return '[{"date":"2026-05-29 08:30:00","event":"Core CPI","country":"US","currency":"USD","actual":"0.2%"}]'

    monkeypatch.setattr(FmpEconomicCalendarHttpClient, "_fetch_public_text_url", fake_fetch)

    response = client.post("/economic-calendar/refresh")

    assert response.status_code == 200
    payload = response.json()
    rendered = repr(payload).lower()
    assert payload["status"] == "refreshed"
    assert payload["data_mode"] == "provider_reference"
    assert payload["source_label"] == "FMP Economic Calendar evaluation"
    assert payload["record_count"] == 1
    assert captured_urls
    assert "test_fmp_key" not in rendered
    assert "apikey" not in rendered


def test_economic_calendar_refresh_requires_local_access(app) -> None:
    client = TestClient(app)

    response = client.post("/economic-calendar/refresh")

    assert response.status_code == 401


def test_economic_calendar_routes_avoid_forbidden_wording(client: TestClient) -> None:
    events_payload = client.get("/economic-calendar/events").json()
    refresh_payload = client.post("/economic-calendar/refresh").json()
    rendered = repr((events_payload, refresh_payload)).lower()
    forbidden_text = (
        "raw_provider_payload",
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
        "buy because",
        "sell because",
    )

    assert not find_forbidden_keys(events_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not find_forbidden_keys(refresh_payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not any(text in rendered for text in forbidden_text)
