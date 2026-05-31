"""Economic calendar contracts, fixtures, adapter, and last-good cache helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.schemas.economic_calendar import EconomicCalendarEventListRead, EconomicCalendarEventRead


_SNAPSHOT_VERSION = 1
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH = _BACKEND_ROOT / "cache" / "economic_calendar_snapshot.json"
FMP_ECONOMIC_CALENDAR_URL = "https://financialmodelingprep.com/api/v3/economic_calendar"

SYNTHETIC_SOURCE_LABEL = "Synthetic economic calendar fixture"
SYNTHETIC_AS_OF_LABEL = "Synthetic fixture · not live calendar data"
SYNTHETIC_FRESHNESS_LABEL = "Synthetic fixture · not live calendar data"
PROVIDER_SOURCE_LABEL = "FMP Economic Calendar evaluation"
PROVIDER_FRESHNESS_LABEL = "Provider reference · not a trading signal"
UNAVAILABLE_SOURCE_LABEL = "Economic calendar unavailable"
UNAVAILABLE_AS_OF_LABEL = "Unavailable"
UNAVAILABLE_FRESHNESS_LABEL = "Unavailable"
DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_WINDOW_START = date(2026, 5, 29)
DEFAULT_WINDOW_END = date(2026, 6, 5)
DEFAULT_LIMITATIONS = (
    "Economic calendar awareness only.",
    "Not a trading signal.",
    "Events are not personalized from portfolio or broker data.",
)
SYNTHETIC_DEMO_NOTICE = "demo · synthetic economic calendar fixture"


class EconomicCalendarRefreshError(RuntimeError):
    """Sanitized refresh error that never includes raw provider payloads."""


class EconomicCalendarPersistenceError(RuntimeError):
    """Sanitized persistence error for normalized economic calendar snapshots."""


class EconomicCalendarProvider(Protocol):
    def snapshot(self, *, window_start: date | None = None, window_end: date | None = None) -> "EconomicCalendarSnapshot":
        """Return normalized public economic calendar records."""


class FmpEconomicCalendarClient(Protocol):
    def fetch_events(self, *, start_date: date, end_date: date) -> Sequence[Mapping[str, Any]]:
        """Fetch FMP-shaped economic calendar rows through an injected boundary."""


@dataclass(frozen=True)
class EconomicCalendarEventRecord:
    event_reference: str
    event_date_label: str
    event_time_label: str
    event_title: str
    event_type: str
    importance: str
    importance_source: str
    country: str
    currency: str
    actual_label: str | None = None
    forecast_label: str | None = None
    previous_label: str | None = None
    unit_label: str | None = None
    source_label: str = SYNTHETIC_SOURCE_LABEL
    freshness_label: str = SYNTHETIC_FRESHNESS_LABEL
    is_trading_signal: bool = False
    data_mode: str = "synthetic"

    def __post_init__(self) -> None:
        if self.is_trading_signal:
            raise ValueError("economic calendar records must not be trading signals")
        if not self.event_reference.startswith("econ_evt_"):
            raise ValueError("economic calendar event_reference must be app-owned and opaque")
        object.__setattr__(self, "event_title", _clean_display_text(self.event_title))
        object.__setattr__(self, "country", _clean_display_text(self.country or "US").upper())
        object.__setattr__(self, "currency", _clean_display_text(self.currency or "USD").upper())


@dataclass(frozen=True)
class EconomicCalendarSnapshot:
    records: tuple[EconomicCalendarEventRecord, ...]
    source_label: str
    as_of_label: str
    freshness_label: str
    window_start: date
    window_end: date
    timezone: str
    importance_source: str
    data_mode: str
    imported_at: datetime
    demo_notice: str | None = None
    limitations: tuple[str, ...] = DEFAULT_LIMITATIONS


class EconomicCalendarSnapshotStore:
    """In-memory last-good economic calendar snapshot boundary."""

    def __init__(self) -> None:
        self._active_snapshot: EconomicCalendarSnapshot | None = None

    @property
    def active_snapshot(self) -> EconomicCalendarSnapshot | None:
        return self._active_snapshot

    def activate(self, snapshot: EconomicCalendarSnapshot) -> None:
        self._active_snapshot = snapshot

    def clear(self) -> None:
        self._active_snapshot = None


GLOBAL_ECONOMIC_CALENDAR_STORE = EconomicCalendarSnapshotStore()
_AUTO_RESTORE_ENABLED = True


class SyntheticEconomicCalendarProvider:
    """Deterministic synthetic provider for default tests and local UI shape."""

    def snapshot(self, *, window_start: date | None = None, window_end: date | None = None) -> EconomicCalendarSnapshot:
        start = window_start or DEFAULT_WINDOW_START
        end = window_end or DEFAULT_WINDOW_END
        records = tuple(record for record in _synthetic_records() if start <= _date_from_label(record.event_date_label) <= end)
        return EconomicCalendarSnapshot(
            records=records,
            source_label=SYNTHETIC_SOURCE_LABEL,
            as_of_label=SYNTHETIC_AS_OF_LABEL,
            freshness_label=SYNTHETIC_FRESHNESS_LABEL,
            window_start=start,
            window_end=end,
            timezone=DEFAULT_TIMEZONE,
            importance_source=_snapshot_importance_source(records),
            data_mode="synthetic",
            imported_at=datetime(2026, 5, 29, 13, 0, tzinfo=UTC),
            demo_notice=SYNTHETIC_DEMO_NOTICE,
        )


class EmptyEconomicCalendarProvider:
    def snapshot(self, *, window_start: date | None = None, window_end: date | None = None) -> EconomicCalendarSnapshot:
        start = window_start or DEFAULT_WINDOW_START
        end = window_end or DEFAULT_WINDOW_END
        return EconomicCalendarSnapshot(
            records=(),
            source_label=SYNTHETIC_SOURCE_LABEL,
            as_of_label=SYNTHETIC_AS_OF_LABEL,
            freshness_label=SYNTHETIC_FRESHNESS_LABEL,
            window_start=start,
            window_end=end,
            timezone=DEFAULT_TIMEZONE,
            importance_source="unavailable",
            data_mode="synthetic",
            imported_at=datetime(2026, 5, 29, 13, 0, tzinfo=UTC),
            demo_notice=SYNTHETIC_DEMO_NOTICE,
        )


class SnapshotEconomicCalendarProvider:
    def __init__(self, snapshot: EconomicCalendarSnapshot) -> None:
        self._snapshot = snapshot

    def snapshot(self, *, window_start: date | None = None, window_end: date | None = None) -> EconomicCalendarSnapshot:
        if window_start is None and window_end is None:
            return self._snapshot
        start = window_start or self._snapshot.window_start
        end = window_end or self._snapshot.window_end
        records = tuple(
            record for record in self._snapshot.records if start <= _date_from_label(record.event_date_label) <= end
        )
        return EconomicCalendarSnapshot(
            records=records,
            source_label=self._snapshot.source_label,
            as_of_label=self._snapshot.as_of_label,
            freshness_label=self._snapshot.freshness_label,
            window_start=start,
            window_end=end,
            timezone=self._snapshot.timezone,
            importance_source=_snapshot_importance_source(records),
            data_mode=self._snapshot.data_mode,
            imported_at=self._snapshot.imported_at,
            demo_notice=self._snapshot.demo_notice,
            limitations=self._snapshot.limitations,
        )


class FmpEconomicCalendarProvider:
    """Map injected FMP-shaped rows into provider-neutral records."""

    def __init__(self, client: FmpEconomicCalendarClient, *, imported_at: datetime | None = None) -> None:
        self._client = client
        self._imported_at = imported_at

    def snapshot(self, *, window_start: date | None = None, window_end: date | None = None) -> EconomicCalendarSnapshot:
        start = window_start or datetime.now(UTC).date()
        end = window_end or start + timedelta(days=7)
        try:
            rows = self._client.fetch_events(start_date=start, end_date=end)
            records = tuple(
                record for index, row in enumerate(rows) if (record := _record_from_fmp_row(row, index=index)) is not None
            )
            imported = self._imported_at or datetime.now(UTC)
            return EconomicCalendarSnapshot(
                records=records,
                source_label=PROVIDER_SOURCE_LABEL,
                as_of_label=f"FMP Economic Calendar imported {imported.isoformat()}",
                freshness_label=PROVIDER_FRESHNESS_LABEL,
                window_start=start,
                window_end=end,
                timezone=DEFAULT_TIMEZONE,
                importance_source=_snapshot_importance_source(records),
                data_mode="provider_reference",
                imported_at=imported,
                demo_notice=None,
                limitations=DEFAULT_LIMITATIONS,
            )
        except Exception as exc:
            raise EconomicCalendarRefreshError("economic calendar refresh failed; last good snapshot was preserved") from exc


class FmpEconomicCalendarHttpClient:
    """Tiny runtime FMP client used only by explicit local-demo refresh."""

    def __init__(
        self,
        *,
        api_key: str,
        fetch_text: Any | None = None,
        endpoint_url: str = FMP_ECONOMIC_CALENDAR_URL,
        timeout_seconds: int = 15,
    ) -> None:
        key = api_key.strip()
        if not key:
            raise EconomicCalendarRefreshError("economic calendar refresh is not configured")
        self._api_key = key
        self._fetch_text = fetch_text or self._fetch_public_text_url
        self._endpoint_url = endpoint_url
        self._timeout_seconds = timeout_seconds

    def fetch_events(self, *, start_date: date, end_date: date) -> Sequence[Mapping[str, Any]]:
        query = urlencode(
            {
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
                "apikey": self._api_key,
            }
        )
        url = f"{self._endpoint_url}?{query}"
        try:
            payload = json.loads(self._fetch_text(url))
        except Exception:
            # Suppress the exception chain: a failing transport/parse exception can
            # embed `apikey=<key>` (the URL is passed to the transport). `from None`
            # keeps the API key out of `__cause__`/`__context__` so it can never
            # reach a traceback or log, even if upstream logging adds `exc_info`.
            raise EconomicCalendarRefreshError("FMP economic calendar fetch failed") from None
        if isinstance(payload, list):
            return tuple(row for row in payload if isinstance(row, Mapping))
        if isinstance(payload, Mapping):
            for key in ("economicCalendar", "calendar", "data"):
                rows = payload.get(key)
                if isinstance(rows, list):
                    return tuple(row for row in rows if isinstance(row, Mapping))
        raise EconomicCalendarRefreshError("FMP economic calendar response was unavailable")

    def _fetch_public_text_url(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": "portfolio-options-agent-economic-calendar/0.1"})
        with urlopen(request, timeout=self._timeout_seconds) as response:  # nosec B310 - explicit opt-in public API fetch
            return response.read().decode("utf-8", errors="replace")


class EconomicCalendarService:
    def __init__(self, provider: EconomicCalendarProvider | None = None) -> None:
        self._provider = provider or default_economic_calendar_provider()

    def list_events(
        self,
        *,
        window_start: date | None = None,
        window_end: date | None = None,
        current_time: datetime | None = None,
    ) -> EconomicCalendarEventListRead:
        try:
            snapshot = self._provider.snapshot(window_start=window_start, window_end=window_end)
        except Exception:
            return unavailable_economic_calendar_read(window_start=window_start, window_end=window_end)
        return read_from_snapshot(snapshot, current_time=current_time)


def default_economic_calendar_provider() -> EconomicCalendarProvider:
    snapshot = get_active_economic_calendar_snapshot()
    if snapshot is not None:
        return SnapshotEconomicCalendarProvider(snapshot)
    return SyntheticEconomicCalendarProvider()


def get_active_economic_calendar_snapshot() -> EconomicCalendarSnapshot | None:
    if _AUTO_RESTORE_ENABLED and GLOBAL_ECONOMIC_CALENDAR_STORE.active_snapshot is None:
        restore_active_economic_calendar_snapshot()
    return GLOBAL_ECONOMIC_CALENDAR_STORE.active_snapshot


def clear_active_economic_calendar_snapshot(*, disable_auto_restore: bool = False) -> None:
    GLOBAL_ECONOMIC_CALENDAR_STORE.clear()
    set_economic_calendar_auto_restore_enabled(not disable_auto_restore)


def set_economic_calendar_auto_restore_enabled(enabled: bool) -> None:
    global _AUTO_RESTORE_ENABLED
    _AUTO_RESTORE_ENABLED = enabled


def read_from_snapshot(
    snapshot: EconomicCalendarSnapshot,
    *,
    current_time: datetime | None = None,
) -> EconomicCalendarEventListRead:
    records = _us_macro_records(snapshot.records, window_start=snapshot.window_start, window_end=snapshot.window_end)
    return EconomicCalendarEventListRead(
        data_mode=snapshot.data_mode,
        source_label=snapshot.source_label,
        as_of_label=snapshot.as_of_label,
        freshness_label=snapshot.freshness_label,
        window_start=snapshot.window_start,
        window_end=snapshot.window_end,
        timezone=snapshot.timezone,
        importance_source=snapshot.importance_source,
        items=tuple(_event_read(record, current_time=current_time, timezone_name=snapshot.timezone) for record in records),
        demo_notice=snapshot.demo_notice,
        is_trading_signal=False,
        limitations=snapshot.limitations,
    )


def resolve_economic_calendar_window(
    *,
    start_date_text: str | None,
    end_date_text: str | None,
    current_date: date,
) -> tuple[date, date]:
    """Resolve and validate a user-selected calendar window."""

    start = _parse_query_date(start_date_text, field_name="start_date") if start_date_text else current_date
    end = _parse_query_date(end_date_text, field_name="end_date") if end_date_text else start
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    return (start, end)


def unavailable_economic_calendar_read(
    *,
    window_start: date | None = None,
    window_end: date | None = None,
) -> EconomicCalendarEventListRead:
    start = window_start or DEFAULT_WINDOW_START
    end = window_end or DEFAULT_WINDOW_END
    return EconomicCalendarEventListRead(
        data_mode="unavailable",
        source_label=UNAVAILABLE_SOURCE_LABEL,
        as_of_label=UNAVAILABLE_AS_OF_LABEL,
        freshness_label=UNAVAILABLE_FRESHNESS_LABEL,
        window_start=start,
        window_end=end,
        timezone=DEFAULT_TIMEZONE,
        importance_source="unavailable",
        items=(),
        demo_notice=None,
        is_trading_signal=False,
        limitations=("Economic calendar is temporarily unavailable.", "Not a trading signal."),
    )


def classify_economic_event(title: str, *, event_type: str | None = None) -> tuple[str, str]:
    normalized = _normalize_event_title(title)
    event_type_normalized = (event_type or "").strip().lower()
    if event_type_normalized == "holiday" or "holiday" in normalized:
        return ("low", "app_classified")
    high_patterns = (
        "fomc",
        "fed rate decision",
        "federal funds rate",
        "rate decision",
        "core cpi",
        " cpi ",
        "consumer price index",
        "core pce",
        " pce ",
        "personal consumption expenditures",
        "nonfarm payrolls",
        "unemployment rate",
        " gdp ",
        "gross domestic product",
        " ism ",
        " pmi ",
        "retail sales",
    )
    if any(pattern in f" {normalized} " for pattern in high_patterns):
        return ("high", "app_classified")
    medium_patterns = (
        "durable goods",
        "jobless claims",
        "initial claims",
        "housing",
        "new home sales",
        "industrial production",
        "consumer confidence",
        "speech",
        "speaks",
        "testimony",
    )
    if event_type_normalized == "speech" or any(pattern in normalized for pattern in medium_patterns):
        return ("medium", "app_classified")
    return ("unknown", "app_classified")


def infer_economic_event_type(title: str) -> str:
    normalized = _normalize_event_title(title)
    if "holiday" in normalized:
        return "holiday"
    if any(term in normalized for term in ("fomc", "fed rate", "rate decision", "central bank")):
        return "central_bank"
    if any(term in normalized for term in ("speech", "speaks", "testimony")):
        return "speech"
    if normalized:
        return "economic_release"
    return "other"


def save_economic_calendar_snapshot(
    snapshot: EconomicCalendarSnapshot,
    *,
    path: Path | str = DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": _SNAPSHOT_VERSION,
        "source_label": snapshot.source_label,
        "as_of_label": snapshot.as_of_label,
        "freshness_label": snapshot.freshness_label,
        "window_start": snapshot.window_start.isoformat(),
        "window_end": snapshot.window_end.isoformat(),
        "timezone": snapshot.timezone,
        "importance_source": snapshot.importance_source,
        "data_mode": snapshot.data_mode,
        "imported_at": snapshot.imported_at.isoformat(),
        "demo_notice": snapshot.demo_notice,
        "limitations": list(snapshot.limitations),
        "records": [_record_payload(record) for record in snapshot.records],
    }
    try:
        tmp_path = target.with_suffix(target.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        tmp_path.replace(target)
    except Exception as exc:
        raise EconomicCalendarPersistenceError("economic calendar snapshot persistence failed") from exc


def load_economic_calendar_snapshot(
    *,
    path: Path | str = DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH,
) -> EconomicCalendarSnapshot | None:
    source = Path(path)
    if not source.exists():
        return None
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        return _snapshot_from_payload(payload)
    except Exception:
        return None


def restore_active_economic_calendar_snapshot(
    *,
    path: Path | str = DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH,
    store: EconomicCalendarSnapshotStore = GLOBAL_ECONOMIC_CALENDAR_STORE,
) -> EconomicCalendarSnapshot | None:
    snapshot = load_economic_calendar_snapshot(path=path)
    if snapshot is None:
        return None
    try:
        store.activate(snapshot)
    except Exception:
        return None
    return snapshot


def refresh_and_persist_economic_calendar_snapshot(
    *,
    provider: EconomicCalendarProvider,
    store: EconomicCalendarSnapshotStore = GLOBAL_ECONOMIC_CALENDAR_STORE,
    snapshot_path: Path | str = DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH,
    window_start: date | None = None,
    window_end: date | None = None,
) -> EconomicCalendarSnapshot:
    """Refresh and persist normalized records, activating only after full success."""

    try:
        snapshot = provider.snapshot(window_start=window_start, window_end=window_end)
        save_economic_calendar_snapshot(snapshot, path=snapshot_path)
        store.activate(snapshot)
        return snapshot
    except Exception as exc:
        raise EconomicCalendarRefreshError("economic calendar refresh failed; last good snapshot was preserved") from exc


def refresh_economic_calendar_unconfigured() -> EconomicCalendarSnapshot:
    """Default protected route runner. It is intentionally disabled until configured."""

    raise EconomicCalendarRefreshError("economic calendar refresh is not configured")


def build_fmp_economic_calendar_refresh_runner_from_environment() -> Any:
    """Build the route refresh runner from backend environment only."""

    api_key = os.environ.get("FMP_API_KEY", "").strip()
    if not api_key:
        return refresh_economic_calendar_unconfigured
    return build_fmp_economic_calendar_refresh_runner(api_key=api_key)


def build_fmp_economic_calendar_refresh_runner(
    *,
    api_key: str | None = None,
    client: FmpEconomicCalendarClient | None = None,
    fetch_text: Any | None = None,
    store: EconomicCalendarSnapshotStore = GLOBAL_ECONOMIC_CALENDAR_STORE,
    snapshot_path: Path | str | None = None,
    now: Any | None = None,
) -> Any:
    """Create an opt-in refresh runner that persists normalized FMP records."""

    def run() -> EconomicCalendarSnapshot:
        current = now() if now is not None else datetime.now(UTC)
        window_start = current.date()
        window_end = window_start + timedelta(days=7)
        fmp_client = client or FmpEconomicCalendarHttpClient(api_key=api_key or "", fetch_text=fetch_text)
        provider = FmpEconomicCalendarProvider(fmp_client, imported_at=current)
        return refresh_and_persist_economic_calendar_snapshot(
            provider=provider,
            store=store,
            snapshot_path=snapshot_path or DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH,
            window_start=window_start,
            window_end=window_end,
        )

    return run


def _event_read(
    record: EconomicCalendarEventRecord,
    *,
    current_time: datetime | None = None,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> EconomicCalendarEventRead:
    event_datetime = _event_datetime_utc(record, timezone_name=timezone_name)
    return EconomicCalendarEventRead(
        event_reference=record.event_reference,
        event_datetime_utc=_isoformat_utc(event_datetime),
        event_has_occurred=_event_has_occurred(event_datetime, current_time=current_time),
        event_date_label=record.event_date_label,
        event_time_label=record.event_time_label,
        event_title=record.event_title,
        event_type=record.event_type,
        importance=record.importance,
        importance_source=record.importance_source,
        country=record.country,
        currency=record.currency,
        actual_label=record.actual_label,
        forecast_label=record.forecast_label,
        previous_label=record.previous_label,
        unit_label=record.unit_label,
        source_label=record.source_label,
        freshness_label=record.freshness_label,
        is_trading_signal=False,
        data_mode=record.data_mode,
    )


def _synthetic_records() -> tuple[EconomicCalendarEventRecord, ...]:
    definitions = (
        ("2026-05-29", "08:30", "Core PCE Price Index", "economic_release", "US", "USD", "0.2%", "0.3%", "0.2%", "%"),
        ("2026-05-30", "14:00", "FOMC Rate Decision", "central_bank", "US", "USD", None, "4.50%", "4.50%", "%"),
        ("2026-06-02", "08:30", "Nonfarm Payrolls", "economic_release", "US", "USD", "185K", "175K", "170K", "jobs"),
        ("2026-06-03", "10:00", "ISM Manufacturing PMI", "economic_release", "US", "USD", "51.2", "50.8", "50.5", "index"),
        ("2026-06-04", "08:30", "Initial Jobless Claims", "economic_release", "US", "USD", "225K", "220K", "218K", "claims"),
        ("2026-06-04", "12:15", "Fed Governor Speech", "speech", "US", "USD", None, None, None, None),
        ("2026-06-05", "09:45", "Regional Business Survey", "economic_release", "US", "USD", None, None, None, "index"),
        ("2026-06-05", "00:00", "Bank Holiday", "holiday", "US", "USD", None, None, None, None),
    )
    records = []
    for index, (event_date, event_time, title, event_type, country, currency, actual, forecast, previous, unit) in enumerate(
        definitions
    ):
        importance, importance_source = classify_economic_event(title, event_type=event_type)
        records.append(
            EconomicCalendarEventRecord(
                event_reference=_event_reference(title=title, event_date_label=event_date, event_time_label=event_time, index=index),
                event_date_label=event_date,
                event_time_label=event_time,
                event_title=title,
                event_type=event_type,
                importance=importance,
                importance_source=importance_source,
                country=country,
                currency=currency,
                actual_label=actual,
                forecast_label=forecast,
                previous_label=previous,
                unit_label=unit,
            )
        )
    return tuple(records)


def _record_from_fmp_row(row: Mapping[str, Any], *, index: int) -> EconomicCalendarEventRecord | None:
    title = _first_string(row, ("event", "eventName", "title", "name"))
    date_text = _first_string(row, ("date", "datetime", "eventDate"))
    if not title or not date_text:
        return None
    parsed = _parse_fmp_datetime(date_text, _first_string(row, ("time", "eventTime")))
    if parsed is None:
        return None
    event_date_label, event_time_label = parsed
    event_type = infer_economic_event_type(title)
    provider_importance = _provider_importance(_first_string(row, ("importance", "impact")))
    if provider_importance is None:
        importance, importance_source = classify_economic_event(title, event_type=event_type)
    else:
        importance, importance_source = provider_importance, "provider"
    return EconomicCalendarEventRecord(
        event_reference=_event_reference(title=title, event_date_label=event_date_label, event_time_label=event_time_label, index=index),
        event_date_label=event_date_label,
        event_time_label=event_time_label,
        event_title=title,
        event_type=event_type,
        importance=importance,
        importance_source=importance_source,
        country=_safe_code(_first_string(row, ("country", "countryCode")) or "US"),
        currency=_safe_code(_first_string(row, ("currency",)) or "USD"),
        actual_label=_safe_value_label(row.get("actual")),
        forecast_label=_safe_value_label(row.get("forecast")),
        previous_label=_safe_value_label(row.get("previous")),
        unit_label=_safe_value_label(row.get("unit")),
        source_label=PROVIDER_SOURCE_LABEL,
        freshness_label=PROVIDER_FRESHNESS_LABEL,
        data_mode="provider_reference",
    )


def _record_payload(record: EconomicCalendarEventRecord) -> dict[str, Any]:
    return {
        "event_reference": record.event_reference,
        "event_date_label": record.event_date_label,
        "event_time_label": record.event_time_label,
        "event_title": record.event_title,
        "event_type": record.event_type,
        "importance": record.importance,
        "importance_source": record.importance_source,
        "country": record.country,
        "currency": record.currency,
        "actual_label": record.actual_label,
        "forecast_label": record.forecast_label,
        "previous_label": record.previous_label,
        "unit_label": record.unit_label,
        "source_label": record.source_label,
        "freshness_label": record.freshness_label,
        "is_trading_signal": False,
        "data_mode": record.data_mode,
    }


def _us_macro_records(
    records: Sequence[EconomicCalendarEventRecord],
    *,
    window_start: date,
    window_end: date,
) -> tuple[EconomicCalendarEventRecord, ...]:
    return tuple(
        record
        for record in records
        if window_start <= _date_from_label(record.event_date_label) <= window_end and _is_us_macro_record(record)
    )


def _snapshot_from_payload(payload: Any) -> EconomicCalendarSnapshot:
    if not isinstance(payload, dict) or payload.get("version") != _SNAPSHOT_VERSION:
        raise ValueError("invalid economic calendar snapshot version")
    records_payload = payload.get("records")
    if not isinstance(records_payload, list):
        raise ValueError("invalid economic calendar snapshot records")
    records = tuple(_record_from_payload(item) for item in records_payload)
    return EconomicCalendarSnapshot(
        records=records,
        source_label=str(payload["source_label"]),
        as_of_label=str(payload["as_of_label"]),
        freshness_label=str(payload["freshness_label"]),
        window_start=date.fromisoformat(str(payload["window_start"])),
        window_end=date.fromisoformat(str(payload["window_end"])),
        timezone=str(payload["timezone"]),
        importance_source=str(payload["importance_source"]),
        data_mode=str(payload["data_mode"]),
        imported_at=datetime.fromisoformat(str(payload["imported_at"])),
        demo_notice=payload.get("demo_notice"),
        limitations=tuple(str(item) for item in payload.get("limitations", DEFAULT_LIMITATIONS)),
    )


def _record_from_payload(payload: Any) -> EconomicCalendarEventRecord:
    if not isinstance(payload, dict):
        raise ValueError("invalid economic calendar record")
    return EconomicCalendarEventRecord(
        event_reference=str(payload["event_reference"]),
        event_date_label=str(payload["event_date_label"]),
        event_time_label=str(payload["event_time_label"]),
        event_title=str(payload["event_title"]),
        event_type=str(payload["event_type"]),
        importance=str(payload["importance"]),
        importance_source=str(payload["importance_source"]),
        country=str(payload["country"]),
        currency=str(payload["currency"]),
        actual_label=_optional_str(payload.get("actual_label")),
        forecast_label=_optional_str(payload.get("forecast_label")),
        previous_label=_optional_str(payload.get("previous_label")),
        unit_label=_optional_str(payload.get("unit_label")),
        source_label=str(payload["source_label"]),
        freshness_label=str(payload["freshness_label"]),
        data_mode=str(payload["data_mode"]),
        is_trading_signal=bool(payload.get("is_trading_signal", False)),
    )


def _snapshot_importance_source(records: Sequence[EconomicCalendarEventRecord]) -> str:
    sources = {record.importance_source for record in records}
    if not sources:
        return "unavailable"
    if sources == {"provider"}:
        return "provider"
    return "app_classified"


def _is_us_macro_record(record: EconomicCalendarEventRecord) -> bool:
    return record.country == "US" or record.currency == "USD"


def _event_reference(*, title: str, event_date_label: str, event_time_label: str, index: int) -> str:
    digest = hashlib.sha256(f"{event_date_label}|{event_time_label}|{title}|{index}".encode("utf-8")).hexdigest()
    return f"econ_evt_{digest[:16]}"


def _normalize_event_title(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", title.lower())).strip()


def _clean_display_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def _date_from_label(value: str) -> date:
    return date.fromisoformat(value)


def _parse_query_date(value: str, *, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be formatted as YYYY-MM-DD") from exc


def _event_datetime_utc(
    record: EconomicCalendarEventRecord,
    *,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> datetime | None:
    if not re.fullmatch(r"\d{2}:\d{2}", record.event_time_label):
        return None
    try:
        hour, minute = (int(part) for part in record.event_time_label.split(":", 1))
        local_timezone = ZoneInfo(timezone_name)
        local_datetime = datetime.combine(
            _date_from_label(record.event_date_label),
            datetime.min.time(),
            tzinfo=local_timezone,
        ).replace(hour=hour, minute=minute)
        return local_datetime.astimezone(UTC)
    except ZoneInfoNotFoundError:
        return None
    except Exception:
        return None


def _isoformat_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _event_has_occurred(value: datetime | None, *, current_time: datetime | None) -> bool | None:
    if value is None:
        return None
    comparison_time = current_time or datetime.now(UTC)
    return value < comparison_time.astimezone(UTC)


def _first_string(row: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _parse_fmp_datetime(date_text: str, time_text: str | None) -> tuple[str, str] | None:
    text = date_text.strip().replace("Z", "+00:00")
    try:
        if "T" in text or re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}(:\d{2})?", text):
            parsed = datetime.fromisoformat(text)
            return (parsed.date().isoformat(), parsed.strftime("%H:%M"))
        parsed_date = date.fromisoformat(text[:10])
        cleaned_time = (time_text or "").strip()
        if cleaned_time and re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", cleaned_time):
            return (parsed_date.isoformat(), cleaned_time[:5].zfill(5))
        return (parsed_date.isoformat(), "Time TBD")
    except Exception:
        return None


def _provider_importance(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"high", "medium", "low"}:
        return normalized
    if normalized in {"3", "red"}:
        return "high"
    if normalized in {"2", "orange", "yellow"}:
        return "medium"
    if normalized in {"1", "green"}:
        return "low"
    return None


def _safe_value_label(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _safe_code(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z]", "", value).upper()
    return cleaned[:3] or "US"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
