from datetime import UTC, date, datetime, timedelta

import pytest

from app.services.economic_calendar import (
    DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH,
    EconomicCalendarEventRecord,
    EconomicCalendarRefreshError,
    EconomicCalendarService,
    EconomicCalendarSnapshot,
    EconomicCalendarSnapshotStore,
    EmptyEconomicCalendarProvider,
    FmpEconomicCalendarHttpClient,
    FmpEconomicCalendarProvider,
    SnapshotEconomicCalendarProvider,
    SyntheticEconomicCalendarProvider,
    build_fmp_economic_calendar_refresh_runner,
    build_fmp_economic_calendar_refresh_runner_from_environment,
    classify_economic_event,
    clear_active_economic_calendar_snapshot,
    load_economic_calendar_snapshot,
    read_from_snapshot,
    refresh_and_persist_economic_calendar_snapshot,
    resolve_economic_calendar_window,
    restore_active_economic_calendar_snapshot,
    save_economic_calendar_snapshot,
    unavailable_economic_calendar_read,
)
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 29, 14, 30, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _clear_economic_calendar_snapshot(monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    clear_active_economic_calendar_snapshot(disable_auto_restore=True)
    yield
    clear_active_economic_calendar_snapshot(disable_auto_restore=True)


def test_synthetic_calendar_contract_contains_safe_macro_events() -> None:
    payload = EconomicCalendarService().list_events(window_start=date(2026, 5, 29), window_end=date(2026, 6, 5))

    assert payload.data_mode == "synthetic"
    assert payload.source_label == "Synthetic economic calendar fixture"
    assert payload.demo_notice == "demo · synthetic economic calendar fixture"
    assert payload.is_trading_signal is False
    assert payload.window_start == date(2026, 5, 29)
    assert payload.window_end == date(2026, 6, 5)
    assert payload.timezone == "America/New_York"
    assert len(payload.items) >= 6
    assert {item.importance for item in payload.items} >= {"high", "medium", "low", "unknown"}
    assert {item.event_type for item in payload.items} >= {"economic_release", "central_bank", "speech", "holiday"}
    assert all(item.is_trading_signal is False for item in payload.items)
    assert payload.items[0].event_datetime_utc == "2026-05-29T12:30:00Z"
    assert payload.items[0].event_has_occurred is not None
    assert not find_forbidden_keys(payload.model_dump(mode="python"), forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)


def test_empty_and_unavailable_states_are_display_safe() -> None:
    empty = EconomicCalendarService(EmptyEconomicCalendarProvider()).list_events()
    unavailable = unavailable_economic_calendar_read()

    assert empty.items == ()
    assert empty.data_mode == "synthetic"
    assert empty.importance_source == "unavailable"
    assert empty.is_trading_signal is False
    assert unavailable.data_mode == "unavailable"
    assert unavailable.items == ()
    assert unavailable.importance_source == "unavailable"
    assert unavailable.is_trading_signal is False


def test_window_resolution_defaults_to_current_date_and_validates_range() -> None:
    assert resolve_economic_calendar_window(start_date_text=None, end_date_text=None, current_date=date(2026, 5, 29)) == (
        date(2026, 5, 29),
        date(2026, 5, 29),
    )
    assert resolve_economic_calendar_window(
        start_date_text="2026-05-29",
        end_date_text="2026-06-04",
        current_date=date(2026, 5, 29),
    ) == (date(2026, 5, 29), date(2026, 6, 4))
    with pytest.raises(ValueError):
        resolve_economic_calendar_window(start_date_text="05/29/2026", end_date_text=None, current_date=date(2026, 5, 29))
    with pytest.raises(ValueError):
        resolve_economic_calendar_window(
            start_date_text="2026-05-30",
            end_date_text="2026-05-29",
            current_date=date(2026, 5, 29),
        )
    # The 7-day cap is removed: wider ordered windows now resolve successfully.
    assert resolve_economic_calendar_window(
        start_date_text="2026-05-29",
        end_date_text="2026-07-15",
        current_date=date(2026, 5, 29),
    ) == (date(2026, 5, 29), date(2026, 7, 15))


def test_us_filtering_and_timing_fields_for_past_future_and_unknown() -> None:
    snapshot = EconomicCalendarSnapshot(
        records=(
            EconomicCalendarEventRecord(
                event_reference="econ_evt_past_us",
                event_date_label="2026-05-29",
                event_time_label="08:30",
                event_title="Retail Sales",
                event_type="economic_release",
                importance="high",
                importance_source="app_classified",
                country="US",
                currency="USD",
            ),
            EconomicCalendarEventRecord(
                event_reference="econ_evt_future_us",
                event_date_label="2026-05-29",
                event_time_label="16:00",
                event_title="Fed Governor Speech",
                event_type="speech",
                importance="medium",
                importance_source="app_classified",
                country="US",
                currency="USD",
            ),
            EconomicCalendarEventRecord(
                event_reference="econ_evt_unknown_us",
                event_date_label="2026-05-29",
                event_time_label="Time TBD",
                event_title="Regional Business Survey",
                event_type="economic_release",
                importance="unknown",
                importance_source="app_classified",
                country="US",
                currency="USD",
            ),
            EconomicCalendarEventRecord(
                event_reference="econ_evt_eu",
                event_date_label="2026-05-29",
                event_time_label="09:00",
                event_title="Euro Area CPI",
                event_type="economic_release",
                importance="high",
                importance_source="app_classified",
                country="EU",
                currency="EUR",
            ),
        ),
        source_label="Synthetic economic calendar fixture",
        as_of_label="Synthetic",
        freshness_label="Synthetic",
        window_start=date(2026, 5, 29),
        window_end=date(2026, 5, 29),
        timezone="America/New_York",
        importance_source="app_classified",
        data_mode="synthetic",
        imported_at=NOW,
        demo_notice="demo",
    )

    payload = read_from_snapshot(snapshot, current_time=datetime(2026, 5, 29, 18, 30, tzinfo=UTC))

    assert [item.event_reference for item in payload.items] == [
        "econ_evt_past_us",
        "econ_evt_future_us",
        "econ_evt_unknown_us",
    ]
    assert payload.items[0].event_datetime_utc == "2026-05-29T12:30:00Z"
    assert payload.items[0].event_has_occurred is True
    assert payload.items[1].event_datetime_utc == "2026-05-29T20:00:00Z"
    assert payload.items[1].event_has_occurred is False
    assert payload.items[2].event_datetime_utc is None
    assert payload.items[2].event_has_occurred is None


@pytest.mark.parametrize(
    ("title", "expected"),
    (
        (" Core CPI m/m ", "high"),
        ("FOMC Rate Decision", "high"),
        ("Nonfarm Payrolls", "high"),
        ("GDP Annualized", "high"),
        ("ISM Manufacturing PMI", "high"),
        ("Retail Sales", "high"),
        ("Initial Jobless Claims", "medium"),
        ("Durable Goods Orders", "medium"),
        ("Consumer Confidence", "medium"),
        ("Bank Holiday", "low"),
        ("Regional Business Survey", "unknown"),
    ),
)
def test_importance_classifier_is_deterministic(title: str, expected: str) -> None:
    assert classify_economic_event(title)[0] == expected
    assert classify_economic_event(title)[1] == "app_classified"


def test_fmp_adapter_maps_injected_rows_and_uses_classifier_when_needed() -> None:
    class FakeClient:
        def fetch_events(self, *, start_date: date, end_date: date):
            assert start_date == date(2026, 5, 29)
            assert end_date == date(2026, 6, 5)
            return (
                {
                    "date": "2026-05-29 08:30:00",
                    "event": "Core PCE Price Index",
                    "country": "US",
                    "currency": "USD",
                    "actual": "0.2%",
                    "forecast": "0.3%",
                    "previous": "0.2%",
                },
                {
                    "date": "2026-06-02T08:30:00",
                    "event": "Durable Goods Orders",
                    "country": "US",
                    "currency": "USD",
                    "importance": "medium",
                    "actual": None,
                    "forecast": "0.5%",
                    "previous": "-0.1%",
                },
                {"date": "bad-date", "event": "raw_payload malformed row"},
            )

    snapshot = FmpEconomicCalendarProvider(FakeClient(), imported_at=NOW).snapshot(
        window_start=date(2026, 5, 29),
        window_end=date(2026, 6, 5),
    )
    payload = read_from_snapshot(snapshot)

    assert payload.data_mode == "provider_reference"
    assert payload.source_label == "FMP Economic Calendar evaluation"
    assert len(payload.items) == 2
    assert payload.items[0].importance == "high"
    assert payload.items[0].importance_source == "app_classified"
    assert payload.items[1].importance == "medium"
    assert payload.items[1].importance_source == "provider"
    assert payload.items[1].actual_label is None
    rendered = repr(payload.model_dump(mode="python")).lower()
    assert "raw_payload" not in rendered


def test_fmp_adapter_failure_is_sanitized() -> None:
    class FailingClient:
        def fetch_events(self, *, start_date: date, end_date: date):
            raise RuntimeError("raw_payload api_key provider_account_id")

    with pytest.raises(EconomicCalendarRefreshError) as exc_info:
        FmpEconomicCalendarProvider(FailingClient()).snapshot()

    rendered = str(exc_info.value).lower()
    assert "raw_payload" not in rendered
    assert "api_key" not in rendered
    assert "provider_account_id" not in rendered


def test_fmp_http_client_uses_injected_transport_and_sanitizes_failures() -> None:
    captured_urls = []

    def fake_fetch(url: str) -> str:
        captured_urls.append(url)
        return '[{"date":"2026-05-29 08:30:00","event":"Retail Sales","country":"US","currency":"USD"}]'

    client = FmpEconomicCalendarHttpClient(api_key="test_key", fetch_text=fake_fetch)
    rows = client.fetch_events(start_date=date(2026, 5, 29), end_date=date(2026, 6, 5))

    assert len(rows) == 1
    assert "apikey=test_key" in captured_urls[0]

    def failing_fetch(_url: str) -> str:
        raise RuntimeError("raw_payload test_key provider trace")

    with pytest.raises(EconomicCalendarRefreshError) as exc_info:
        FmpEconomicCalendarHttpClient(api_key="test_key", fetch_text=failing_fetch).fetch_events(
            start_date=date(2026, 5, 29),
            end_date=date(2026, 6, 5),
        )
    rendered = str(exc_info.value).lower()
    assert "raw_payload" not in rendered
    assert "test_key" not in rendered
    assert "provider trace" not in rendered
    # I1 regression: the API-key-bearing URL/transport exception must not be
    # retained in the chain, so a key can never surface in a traceback/log.
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True


def test_environment_refresh_runner_missing_key_is_safe_failure(monkeypatch) -> None:
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    runner = build_fmp_economic_calendar_refresh_runner_from_environment()

    with pytest.raises(EconomicCalendarRefreshError):
        runner()


def test_fmp_refresh_runner_with_injected_client_persists_provider_reference(tmp_path) -> None:
    class FakeClient:
        def fetch_events(self, *, start_date: date, end_date: date):
            assert start_date == date(2026, 5, 29)
            assert end_date == date(2026, 6, 5)
            return (
                {
                    "date": "2026-05-29 08:30:00",
                    "event": "Retail Sales",
                    "country": "US",
                    "currency": "USD",
                    "actual": "0.4%",
                    "forecast": "0.3%",
                    "previous": "0.1%",
                },
            )

    path = tmp_path / "economic_calendar_snapshot.json"
    store = EconomicCalendarSnapshotStore()
    runner = build_fmp_economic_calendar_refresh_runner(
        client=FakeClient(),
        store=store,
        snapshot_path=path,
        now=lambda: NOW,
    )

    snapshot = runner()
    payload = EconomicCalendarService().list_events()

    assert snapshot.data_mode == "provider_reference"
    assert store.active_snapshot is snapshot
    assert path.exists()
    assert payload.data_mode == "synthetic"
    store.activate(snapshot)
    provider_payload = read_from_snapshot(snapshot).model_dump(mode="python")
    rendered = repr(provider_payload).lower()
    assert provider_payload["data_mode"] == "provider_reference"
    assert "api_key" not in rendered
    assert "raw_payload" not in rendered


def test_refresh_cache_read_filters_to_requested_window(tmp_path) -> None:
    class FakeProvider:
        def snapshot(self, *, window_start=None, window_end=None):
            return EconomicCalendarSnapshot(
                records=(
                    EconomicCalendarEventRecord(
                        event_reference="econ_evt_day_one",
                        event_date_label="2026-05-29",
                        event_time_label="08:30",
                        event_title="Core CPI",
                        event_type="economic_release",
                        importance="high",
                        importance_source="app_classified",
                        country="US",
                        currency="USD",
                    ),
                    EconomicCalendarEventRecord(
                        event_reference="econ_evt_day_two",
                        event_date_label="2026-05-30",
                        event_time_label="08:30",
                        event_title="Retail Sales",
                        event_type="economic_release",
                        importance="high",
                        importance_source="app_classified",
                        country="US",
                        currency="USD",
                    ),
                ),
                source_label="FMP Economic Calendar evaluation",
                as_of_label="FMP Economic Calendar imported 2026-05-29T14:30:00+00:00",
                freshness_label="Provider reference · not a trading signal",
                window_start=date(2026, 5, 29),
                window_end=date(2026, 5, 30),
                timezone="America/New_York",
                importance_source="app_classified",
                data_mode="provider_reference",
                imported_at=NOW,
            )

    store = EconomicCalendarSnapshotStore()
    snapshot = refresh_and_persist_economic_calendar_snapshot(
        provider=FakeProvider(),
        store=store,
        snapshot_path=tmp_path / "calendar.json",
        window_start=date(2026, 5, 29),
        window_end=date(2026, 5, 30),
    )
    payload = EconomicCalendarService(provider=SnapshotEconomicCalendarProvider(snapshot)).list_events(
        window_start=date(2026, 5, 30),
        window_end=date(2026, 5, 30),
        current_time=NOW,
    )

    assert [item.event_reference for item in payload.items] == ["econ_evt_day_two"]


def test_snapshot_save_load_and_restore_round_trip(tmp_path) -> None:
    snapshot = SyntheticEconomicCalendarProvider().snapshot()
    path = tmp_path / "economic_calendar_snapshot.json"

    save_economic_calendar_snapshot(snapshot, path=path)
    loaded = load_economic_calendar_snapshot(path=path)
    store = EconomicCalendarSnapshotStore()
    restored = restore_active_economic_calendar_snapshot(path=path, store=store)

    assert loaded is not None
    assert loaded.source_label == snapshot.source_label
    assert len(loaded.records) == len(snapshot.records)
    assert restored is store.active_snapshot
    assert DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH.parts[-3:] == ("backend", "cache", "economic_calendar_snapshot.json")


def test_malformed_cache_falls_back_to_none(tmp_path) -> None:
    path = tmp_path / "economic_calendar_snapshot.json"
    path.write_text('{"version": 999, "raw_payload": "bad"}', encoding="utf-8")

    assert load_economic_calendar_snapshot(path=path) is None


def test_refresh_success_persists_and_failure_preserves_last_good(tmp_path) -> None:
    path = tmp_path / "economic_calendar_snapshot.json"
    store = EconomicCalendarSnapshotStore()
    good = refresh_and_persist_economic_calendar_snapshot(
        provider=SyntheticEconomicCalendarProvider(),
        store=store,
        snapshot_path=path,
    )

    class FailingProvider:
        def snapshot(self, *, window_start=None, window_end=None):
            raise RuntimeError("raw_payload secret provider trace")

    with pytest.raises(EconomicCalendarRefreshError) as exc_info:
        refresh_and_persist_economic_calendar_snapshot(provider=FailingProvider(), store=store, snapshot_path=path)

    assert store.active_snapshot is good
    assert load_economic_calendar_snapshot(path=path) is not None
    rendered = str(exc_info.value).lower()
    assert "raw_payload" not in rendered
    assert "secret" not in rendered


def test_calendar_payloads_exclude_forbidden_wording() -> None:
    payload = EconomicCalendarService().list_events().model_dump(mode="python")
    rendered = repr(payload).lower()
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

    assert not find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    assert not any(text in rendered for text in forbidden_text)
