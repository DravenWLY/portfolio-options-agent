"""Economic calendar contracts, fixtures, adapter, and last-good cache helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.schemas.economic_calendar import EconomicCalendarEventListRead, EconomicCalendarEventRead


_SNAPSHOT_VERSION = 1
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH = _BACKEND_ROOT / "cache" / "economic_calendar_snapshot.json"
FMP_ECONOMIC_CALENDAR_URL = "https://financialmodelingprep.com/api/v3/economic_calendar"
FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_RELEASES_DATES_URL = "https://api.stlouisfed.org/fred/releases/dates"
FRED_RELEASE_DATES_URL = "https://api.stlouisfed.org/fred/release/dates"
FRED_NOTICE = "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis."

SYNTHETIC_SOURCE_LABEL = "Synthetic economic calendar fixture"
SYNTHETIC_AS_OF_LABEL = "Synthetic fixture · not live calendar data"
SYNTHETIC_FRESHNESS_LABEL = "Synthetic fixture · not live calendar data"
PROVIDER_SOURCE_LABEL = "FMP Economic Calendar evaluation"
PROVIDER_FRESHNESS_LABEL = "Provider reference · not a trading signal"
FRED_SOURCE_LABEL = "FRED macro snapshot"
FRED_FRESHNESS_LABEL = "FRED provider reference · not a trading signal"
FRED_THROTTLED_MESSAGE = "FRED macro data request was throttled"
FRED_PARTIAL_LIMITATION = "Some FRED macro series were unavailable during refresh."
FRED_RELEASE_DATE_LIMITATION = "FRED release dates are source-published and may not match exact FRED data availability."
FRED_RELEASE_VALUE_LIMITATION = "FRED release-calendar rows do not include forecast, actual, or previous values."
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


class FredEconomicCalendarClient(Protocol):
    def fetch_release_dates(
        self,
        *,
        start_date: date,
        end_date: date,
        include_no_data: bool = True,
        limit: int = 1000,
    ) -> Sequence[Mapping[str, Any]]:
        """Fetch FRED-shaped release-calendar rows through an injected boundary."""

    def fetch_release_dates_for_release(
        self,
        *,
        release_id: int,
        start_date: date,
        end_date: date,
        include_no_data: bool = True,
        limit: int = 1000,
    ) -> Sequence[Mapping[str, Any]]:
        """Fetch release-calendar rows for one FRED release through an injected boundary."""

    def fetch_observations(self, *, series_id: str, limit: int = 2) -> Sequence[Mapping[str, Any]]:
        """Fetch FRED-shaped observations through an injected boundary."""


@dataclass(frozen=True)
class FredMacroSeriesDefinition:
    series_id: str
    title: str
    event_type: str
    importance: str
    unit_label: str
    caveat: str | None = None


@dataclass(frozen=True)
class FredMacroReleaseDefinition:
    release_id: int
    title: str
    event_type: str
    importance: str


DEFAULT_FRED_MACRO_RELEASES = (
    FredMacroReleaseDefinition(10, "Consumer Price Index", "economic_release", "high"),
    FredMacroReleaseDefinition(54, "Personal Income and Outlays", "economic_release", "high"),
    FredMacroReleaseDefinition(53, "Gross Domestic Product", "economic_release", "high"),
    FredMacroReleaseDefinition(50, "Employment Situation", "economic_release", "high"),
    FredMacroReleaseDefinition(180, "Unemployment Insurance Weekly Claims Report", "economic_release", "medium"),
    FredMacroReleaseDefinition(9, "Advance Monthly Sales for Retail and Food Services", "economic_release", "high"),
    FredMacroReleaseDefinition(95, "Manufacturer's Shipments, Inventories, and Orders (M3) Survey", "economic_release", "medium"),
)


DEFAULT_FRED_MACRO_SERIES = (
    FredMacroSeriesDefinition("CPIAUCSL", "Consumer Price Index", "economic_release", "high", "index"),
    FredMacroSeriesDefinition("CPILFESL", "Core Consumer Price Index", "economic_release", "high", "index"),
    FredMacroSeriesDefinition("PCEPI", "PCE Price Index", "economic_release", "high", "index"),
    FredMacroSeriesDefinition("PCEPILFE", "Core PCE Price Index", "economic_release", "high", "index"),
    FredMacroSeriesDefinition("GDP", "Gross Domestic Product", "economic_release", "high", "billions of dollars"),
    FredMacroSeriesDefinition("A191RL1Q225SBEA", "Real GDP Growth", "economic_release", "high", "percent change"),
    FredMacroSeriesDefinition("PAYEMS", "Total Nonfarm Payrolls", "economic_release", "high", "thousands"),
    FredMacroSeriesDefinition("UNRATE", "Unemployment Rate", "economic_release", "high", "percent"),
    FredMacroSeriesDefinition("ICSA", "Initial Jobless Claims", "economic_release", "medium", "claims"),
    FredMacroSeriesDefinition("RSAFS", "Retail Sales", "economic_release", "high", "millions of dollars"),
    FredMacroSeriesDefinition("DGORDER", "Durable Goods Orders", "economic_release", "medium", "millions of dollars"),
    FredMacroSeriesDefinition("DGS2", "2-Year Treasury Yield", "other", "low", "percent"),
    FredMacroSeriesDefinition("DGS10", "10-Year Treasury Yield", "other", "low", "percent"),
    FredMacroSeriesDefinition("T10Y2Y", "10-Year Minus 2-Year Treasury Spread", "other", "low", "percent"),
    FredMacroSeriesDefinition("DFF", "Effective Federal Funds Rate", "central_bank", "medium", "percent"),
    FredMacroSeriesDefinition("DFEDTARU", "Federal Funds Target Range Upper Limit", "central_bank", "medium", "percent"),
    FredMacroSeriesDefinition("DFEDTARL", "Federal Funds Target Range Lower Limit", "central_bank", "medium", "percent"),
)


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


class FredEconomicCalendarHttpClient:
    """Tiny runtime FRED client used only by explicit local-demo refresh."""

    def __init__(
        self,
        *,
        api_key: str,
        fetch_text: Any | None = None,
        endpoint_url: str = FRED_OBSERVATIONS_URL,
        releases_dates_url: str = FRED_RELEASES_DATES_URL,
        release_dates_url: str = FRED_RELEASE_DATES_URL,
        timeout_seconds: int = 15,
        min_interval_seconds: float = 1.1,
        max_retries: int = 2,
        retry_backoff_seconds: float = 1.25,
        sleep: Any | None = None,
    ) -> None:
        key = api_key.strip()
        if not key:
            raise EconomicCalendarRefreshError("economic calendar refresh is not configured")
        self._api_key = key
        self._fetch_text = fetch_text or self._fetch_public_text_url
        self._endpoint_url = endpoint_url
        self._releases_dates_url = releases_dates_url
        self._release_dates_url = release_dates_url
        self._timeout_seconds = timeout_seconds
        self._min_interval_seconds = min_interval_seconds
        self._max_retries = max(0, max_retries)
        self._retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self._sleep = sleep or time.sleep
        self._last_request_at: float | None = None

    def fetch_release_dates(
        self,
        *,
        start_date: date,
        end_date: date,
        include_no_data: bool = True,
        limit: int = 1000,
    ) -> Sequence[Mapping[str, Any]]:
        page_limit = max(1, min(limit, 1000))
        rows: list[Mapping[str, Any]] = []
        offset = 0
        while True:
            payload = self._fetch_release_dates_page(
                start_date=start_date,
                end_date=end_date,
                include_no_data=include_no_data,
                limit=page_limit,
                offset=offset,
            )
            release_dates = payload.get("release_dates") if isinstance(payload, Mapping) else None
            if not isinstance(release_dates, list):
                raise EconomicCalendarRefreshError("FRED macro data response was unavailable")
            page_rows = tuple(row for row in release_dates if isinstance(row, Mapping))
            rows.extend(page_rows)
            count = _safe_int(payload.get("count"))
            if not page_rows or count is None or offset + len(page_rows) >= count:
                return tuple(rows)
            offset += len(page_rows)

    def fetch_release_dates_for_release(
        self,
        *,
        release_id: int,
        start_date: date,
        end_date: date,
        include_no_data: bool = True,
        limit: int = 1000,
    ) -> Sequence[Mapping[str, Any]]:
        page_limit = max(1, min(limit, 1000))
        rows: list[Mapping[str, Any]] = []
        offset = 0
        while True:
            payload = self._fetch_release_dates_for_release_page(
                release_id=release_id,
                start_date=start_date,
                end_date=end_date,
                include_no_data=include_no_data,
                limit=page_limit,
                offset=offset,
            )
            release_dates = payload.get("release_dates") if isinstance(payload, Mapping) else None
            if not isinstance(release_dates, list):
                raise EconomicCalendarRefreshError("FRED macro data response was unavailable")
            page_rows = tuple(row for row in release_dates if isinstance(row, Mapping))
            rows.extend(page_rows)
            count = _safe_int(payload.get("count"))
            if not page_rows or count is None or offset + len(page_rows) >= count:
                return tuple(rows)
            offset += len(page_rows)

    def _fetch_release_dates_page(
        self,
        *,
        start_date: date,
        end_date: date,
        include_no_data: bool,
        limit: int,
        offset: int,
    ) -> Mapping[str, Any]:
        query = urlencode(
            {
                "api_key": self._api_key,
                "file_type": "json",
                "realtime_start": start_date.isoformat(),
                "realtime_end": end_date.isoformat(),
                "include_release_dates_with_no_data": "true" if include_no_data else "false",
                "sort_order": "asc",
                "limit": str(limit),
                "offset": str(offset),
            }
        )
        return self._fetch_fred_json(f"{self._releases_dates_url}?{query}")

    def _fetch_release_dates_for_release_page(
        self,
        *,
        release_id: int,
        start_date: date,
        end_date: date,
        include_no_data: bool,
        limit: int,
        offset: int,
    ) -> Mapping[str, Any]:
        query = urlencode(
            {
                "release_id": str(release_id),
                "api_key": self._api_key,
                "file_type": "json",
                "realtime_start": start_date.isoformat(),
                "realtime_end": end_date.isoformat(),
                "include_release_dates_with_no_data": "true" if include_no_data else "false",
                "sort_order": "asc",
                "limit": str(limit),
                "offset": str(offset),
            }
        )
        return self._fetch_fred_json(f"{self._release_dates_url}?{query}")

    def fetch_observations(self, *, series_id: str, limit: int = 2) -> Sequence[Mapping[str, Any]]:
        query = urlencode(
            {
                "series_id": series_id,
                "api_key": self._api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": str(limit),
            }
        )
        payload = self._fetch_fred_json(f"{self._endpoint_url}?{query}")
        observations = payload.get("observations") if isinstance(payload, Mapping) else None
        if isinstance(observations, list):
            return tuple(row for row in observations if isinstance(row, Mapping))
        raise EconomicCalendarRefreshError("FRED macro data response was unavailable")

    def _fetch_fred_json(self, url: str) -> Mapping[str, Any]:
        for attempt in range(self._max_retries + 1):
            self._pause_if_needed()
            fetch_error_message: str | None = None
            try:
                text_payload = self._fetch_text(url)
            except EconomicCalendarRefreshError as exc:
                fetch_error_message = FRED_THROTTLED_MESSAGE if str(exc) == FRED_THROTTLED_MESSAGE else "FRED macro data fetch failed"
            except Exception:
                fetch_error_message = "FRED macro data fetch failed"
            if fetch_error_message is not None:
                if fetch_error_message == FRED_THROTTLED_MESSAGE and attempt < self._max_retries:
                    self._pause_before_retry(attempt)
                    continue
                raise EconomicCalendarRefreshError(fetch_error_message)
            parse_failed = False
            try:
                payload = json.loads(text_payload)
            except Exception:
                parse_failed = True
            if parse_failed:
                raise EconomicCalendarRefreshError("FRED macro data fetch failed")
            if isinstance(payload, Mapping) and payload.get("error_code") == 429:
                if attempt < self._max_retries:
                    self._pause_before_retry(attempt)
                    continue
                raise EconomicCalendarRefreshError(FRED_THROTTLED_MESSAGE)
            if isinstance(payload, Mapping):
                return payload
            raise EconomicCalendarRefreshError("FRED macro data response was unavailable")
        raise EconomicCalendarRefreshError(FRED_THROTTLED_MESSAGE)

    def _pause_if_needed(self) -> None:
        current = time.monotonic()
        if self._last_request_at is not None:
            elapsed = current - self._last_request_at
            if elapsed < self._min_interval_seconds:
                self._sleep(self._min_interval_seconds - elapsed)
        self._last_request_at = time.monotonic()

    def _pause_before_retry(self, attempt: int) -> None:
        self._sleep(self._retry_backoff_seconds * (attempt + 1))

    def _fetch_public_text_url(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": "portfolio-options-agent-economic-calendar/0.1"})
        http_error_code: int | None = None
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:  # nosec B310 - explicit opt-in public API fetch
                return response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            http_error_code = exc.code
        if http_error_code == 429:
            raise EconomicCalendarRefreshError(FRED_THROTTLED_MESSAGE)
        raise EconomicCalendarRefreshError("FRED macro data fetch failed")


class FredEconomicCalendarProvider:
    """Map FRED observations into provider-neutral macro awareness records."""

    def __init__(
        self,
        client: FredEconomicCalendarClient,
        *,
        release_registry: Sequence[FredMacroReleaseDefinition] = DEFAULT_FRED_MACRO_RELEASES,
        registry: Sequence[FredMacroSeriesDefinition] = DEFAULT_FRED_MACRO_SERIES,
        imported_at: datetime | None = None,
    ) -> None:
        self._client = client
        self._release_registry = tuple(release_registry)
        self._registry = tuple(registry)
        self._imported_at = imported_at

    def snapshot(self, *, window_start: date | None = None, window_end: date | None = None) -> EconomicCalendarSnapshot:
        imported = self._imported_at or datetime.now(UTC)
        start = window_start or date(imported.year, 1, 1)
        end = window_end or date(imported.year, 12, 31)
        if self._release_registry:
            release_records = self._release_calendar_records(window_start=start, window_end=end)
            if release_records:
                return EconomicCalendarSnapshot(
                    records=release_records,
                    source_label=FRED_SOURCE_LABEL,
                    as_of_label=f"FRED macro release calendar imported {imported.isoformat()}",
                    freshness_label=FRED_FRESHNESS_LABEL,
                    window_start=start,
                    window_end=end,
                    timezone=DEFAULT_TIMEZONE,
                    importance_source=_snapshot_importance_source(release_records),
                    data_mode="provider_reference",
                    imported_at=imported,
                    demo_notice=None,
                    limitations=DEFAULT_LIMITATIONS
                    + (FRED_NOTICE, FRED_RELEASE_DATE_LIMITATION, FRED_RELEASE_VALUE_LIMITATION),
                )
            raise EconomicCalendarRefreshError("economic calendar refresh failed; last good snapshot was preserved")

        records = []
        failed_count = 0
        for index, definition in enumerate(self._registry):
            try:
                observations = self._client.fetch_observations(series_id=definition.series_id, limit=2)
                record = _record_from_fred_observations(definition, observations, imported_at=imported, index=index)
            except Exception:
                failed_count += 1
                continue
            if record is not None:
                records.append(record)
        if not records:
            raise EconomicCalendarRefreshError("economic calendar refresh failed; last good snapshot was preserved")
        limitations = DEFAULT_LIMITATIONS + (FRED_NOTICE,)
        if failed_count:
            limitations = limitations + (FRED_PARTIAL_LIMITATION,)
        return EconomicCalendarSnapshot(
            records=tuple(records),
            source_label=FRED_SOURCE_LABEL,
            as_of_label=f"FRED macro snapshot imported {imported.isoformat()}",
            freshness_label=FRED_FRESHNESS_LABEL,
            window_start=start,
            window_end=end,
            timezone=DEFAULT_TIMEZONE,
            importance_source=_snapshot_importance_source(tuple(records)),
            data_mode="provider_reference",
            imported_at=imported,
            demo_notice=None,
            limitations=limitations,
        )

    def _release_calendar_records(self, *, window_start: date, window_end: date) -> tuple[EconomicCalendarEventRecord, ...]:
        records = []
        for definition in self._release_registry:
            try:
                rows = self._client.fetch_release_dates_for_release(
                    release_id=definition.release_id,
                    start_date=window_start,
                    end_date=window_end,
                    include_no_data=True,
                )
            except Exception:
                continue
            for row in rows:
                if _safe_int(row.get("release_id")) != definition.release_id:
                    continue
                record = _record_from_fred_release_date(definition, row, index=len(records))
                if record is not None:
                    records.append(record)
        return tuple(records)


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
    except Exception:
        pass
    raise EconomicCalendarRefreshError("economic calendar refresh failed; last good snapshot was preserved")


def refresh_economic_calendar_unconfigured() -> EconomicCalendarSnapshot:
    """Default protected route runner. It is intentionally disabled until configured."""

    raise EconomicCalendarRefreshError("economic calendar refresh is not configured")


def build_fmp_economic_calendar_refresh_runner_from_environment() -> Any:
    """Build the route refresh runner from backend environment only."""

    api_key = os.environ.get("FMP_API_KEY", "").strip()
    if not api_key:
        return refresh_economic_calendar_unconfigured
    return build_fmp_economic_calendar_refresh_runner(api_key=api_key)


def build_fred_economic_calendar_refresh_runner_from_environment() -> Any:
    """Build the route refresh runner from backend FRED environment only."""

    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key:
        return refresh_economic_calendar_unconfigured
    return build_fred_economic_calendar_refresh_runner(api_key=api_key)


def build_fred_economic_calendar_refresh_runner(
    *,
    api_key: str | None = None,
    client: FredEconomicCalendarClient | None = None,
    fetch_text: Any | None = None,
    release_registry: Sequence[FredMacroReleaseDefinition] = DEFAULT_FRED_MACRO_RELEASES,
    registry: Sequence[FredMacroSeriesDefinition] = DEFAULT_FRED_MACRO_SERIES,
    store: EconomicCalendarSnapshotStore = GLOBAL_ECONOMIC_CALENDAR_STORE,
    snapshot_path: Path | str | None = None,
    now: Any | None = None,
) -> Any:
    """Create an opt-in refresh runner that persists normalized FRED records."""

    def run() -> EconomicCalendarSnapshot:
        current = now() if now is not None else datetime.now(UTC)
        fred_client = client or FredEconomicCalendarHttpClient(api_key=api_key or "", fetch_text=fetch_text)
        provider = FredEconomicCalendarProvider(
            fred_client,
            release_registry=release_registry,
            registry=registry,
            imported_at=current,
        )
        return refresh_and_persist_economic_calendar_snapshot(
            provider=provider,
            store=store,
            snapshot_path=snapshot_path or DEFAULT_ECONOMIC_CALENDAR_SNAPSHOT_PATH,
            window_start=date(current.year, 1, 1),
            window_end=date(current.year, 12, 31),
        )

    return run


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


def _record_from_fred_observations(
    definition: FredMacroSeriesDefinition,
    observations: Sequence[Mapping[str, Any]],
    *,
    imported_at: datetime,
    index: int,
) -> EconomicCalendarEventRecord | None:
    valid_observations = tuple(
        observation
        for observation in observations
        if _safe_value_label(observation.get("value")) is not None and _first_string(observation, ("date",)) is not None
    )
    if not valid_observations:
        return None
    latest = valid_observations[0]
    previous = valid_observations[1] if len(valid_observations) > 1 else None
    latest_date = _first_string(latest, ("date",)) or "date unavailable"
    try:
        observation_date_label = date.fromisoformat(latest_date).isoformat()
    except ValueError:
        return None
    latest_value = _safe_value_label(latest.get("value"))
    previous_date = _first_string(previous, ("date",)) if previous is not None else None
    previous_value = _safe_value_label(previous.get("value")) if previous is not None else None
    if latest_value is None:
        return None
    return EconomicCalendarEventRecord(
        event_reference=_event_reference(
            title=definition.series_id,
            event_date_label=observation_date_label,
            event_time_label="Time TBD",
            index=index,
        ),
        event_date_label=observation_date_label,
        event_time_label="Time TBD",
        event_title=definition.title,
        event_type=definition.event_type,
        importance=definition.importance,
        importance_source="app_classified",
        country="US",
        currency="USD",
        actual_label=f"{latest_value} (obs {latest_date})",
        forecast_label=None,
        previous_label=f"{previous_value} (obs {previous_date})" if previous_value is not None and previous_date else None,
        unit_label=definition.unit_label,
        source_label=FRED_SOURCE_LABEL,
        freshness_label=FRED_FRESHNESS_LABEL,
        data_mode="provider_reference",
    )


def _record_from_fred_release_date(
    definition: FredMacroReleaseDefinition,
    row: Mapping[str, Any],
    *,
    index: int,
) -> EconomicCalendarEventRecord | None:
    release_date_label = _first_string(row, ("date",))
    if release_date_label is None:
        return None
    try:
        release_date_label = date.fromisoformat(release_date_label).isoformat()
    except ValueError:
        return None
    release_name = _safe_value_label(row.get("release_name")) or definition.title
    return EconomicCalendarEventRecord(
        event_reference=_event_reference(
            title=f"fred_release_{definition.release_id}",
            event_date_label=release_date_label,
            event_time_label="Time TBD",
            index=index,
        ),
        event_date_label=release_date_label,
        event_time_label="Time TBD",
        event_title=release_name,
        event_type=definition.event_type,
        importance=definition.importance,
        importance_source="app_classified",
        country="US",
        currency="USD",
        actual_label=None,
        forecast_label=None,
        previous_label=None,
        unit_label=None,
        source_label=FRED_SOURCE_LABEL,
        freshness_label=FRED_FRESHNESS_LABEL,
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
        if stripped == ".":
            return None
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


def _safe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None
