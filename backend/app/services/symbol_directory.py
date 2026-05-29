"""Nasdaq-style symbol directory parsing and refresh helpers.

This module handles public symbol-reference data only. It does not fetch
quotes, broker data, options chains, recommendations, or order eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.request import Request, urlopen

from app.services.symbols import SymbolRecord


NASDAQ_TRADED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

_NASDAQ_SOURCE_LABEL = "Nasdaq Symbol Directory"
_NASDAQ_EXCHANGE = "NASDAQ"
_SNAPSHOT_VERSION = 1
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SYMBOL_DIRECTORY_SNAPSHOT_PATH = _BACKEND_ROOT / "cache" / "symbol_directory_snapshot.json"
_OTHER_LISTED_EXCHANGES = {
    "A": "NYSEAMERICAN",
    "N": "NYSE",
    "P": "NYSEARCA",
    "Q": "NASDAQ",
    "Z": "BATS",
    "V": "IEX",
}


class SymbolDirectoryRefreshError(RuntimeError):
    """Sanitized refresh error that never includes raw file/provider payloads."""


class SymbolDirectoryPersistenceError(RuntimeError):
    """Sanitized persistence error for normalized symbol snapshots."""


@dataclass(frozen=True)
class NasdaqSymbolDirectorySource:
    name: str
    url: str


@dataclass(frozen=True)
class SymbolDirectoryParseResult:
    records: tuple[SymbolRecord, ...]
    as_of_label: str


@dataclass(frozen=True)
class SymbolDirectorySnapshot:
    records: tuple[SymbolRecord, ...]
    source_label: str
    as_of_label: str
    imported_at: datetime


class SymbolDirectorySnapshotStore:
    """In-memory last-good symbol directory snapshot boundary."""

    def __init__(self) -> None:
        self._active_snapshot: SymbolDirectorySnapshot | None = None

    @property
    def active_snapshot(self) -> SymbolDirectorySnapshot | None:
        return self._active_snapshot

    def activate(self, snapshot: SymbolDirectorySnapshot) -> None:
        if not snapshot.records:
            raise ValueError("symbol directory snapshot must contain at least one normalized record")
        self._active_snapshot = snapshot

    def clear(self) -> None:
        self._active_snapshot = None


class SymbolDirectoryRefreshJob:
    """Dependency-free scheduled refresh hook for local deployment wiring."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        interval: timedelta = timedelta(days=1),
        refresh: Callable[[], SymbolDirectorySnapshot],
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.enabled = enabled
        self.interval = interval
        self._refresh = refresh
        self._now = now or (lambda: datetime.now(UTC))
        self.last_attempt_at: datetime | None = None

    def run_pending(self) -> SymbolDirectorySnapshot | None:
        if not self.enabled:
            return None
        current = self._now()
        if self.last_attempt_at is not None and current - self.last_attempt_at < self.interval:
            return None
        self.last_attempt_at = current
        return self._refresh()


GLOBAL_SYMBOL_DIRECTORY_STORE = SymbolDirectorySnapshotStore()
_AUTO_RESTORE_ENABLED = True

DEFAULT_NASDAQ_SYMBOL_DIRECTORY_SOURCES = (
    NasdaqSymbolDirectorySource(name="nasdaqtraded", url=NASDAQ_TRADED_URL),
)


def get_active_symbol_directory_snapshot() -> SymbolDirectorySnapshot | None:
    if _AUTO_RESTORE_ENABLED and GLOBAL_SYMBOL_DIRECTORY_STORE.active_snapshot is None:
        restore_active_symbol_directory_snapshot()
    return GLOBAL_SYMBOL_DIRECTORY_STORE.active_snapshot


def clear_active_symbol_directory_snapshot(*, disable_auto_restore: bool = False) -> None:
    GLOBAL_SYMBOL_DIRECTORY_STORE.clear()
    set_symbol_directory_auto_restore_enabled(not disable_auto_restore)


def set_symbol_directory_auto_restore_enabled(enabled: bool) -> None:
    global _AUTO_RESTORE_ENABLED
    _AUTO_RESTORE_ENABLED = enabled


def parse_nasdaq_symbol_directory_file(path: Path | str) -> SymbolDirectoryParseResult:
    file_path = Path(path)
    return parse_nasdaq_symbol_directory_text(file_path.read_text(encoding="utf-8"))


def parse_nasdaq_symbol_directory_text(text: str) -> SymbolDirectoryParseResult:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return SymbolDirectoryParseResult(records=(), as_of_label="Nasdaq Symbol Directory file time unavailable")

    header = lines[0].split("|")
    columns = {name.strip().lower(): index for index, name in enumerate(header)}
    records: list[SymbolRecord] = []
    file_time_label = "Nasdaq Symbol Directory file time unavailable"

    for line in lines[1:]:
        if line.lower().startswith("file creation time:"):
            file_time_label = f"Nasdaq Symbol Directory file time {line.split(':', 1)[1].strip()}"
            continue
        row = line.split("|")
        record = _parse_directory_row(row, columns)
        if record is not None:
            records.append(record)

    return SymbolDirectoryParseResult(records=tuple(records), as_of_label=file_time_label)


def import_nasdaq_symbol_directory_files(
    paths: Iterable[Path | str],
    *,
    imported_at: datetime | None = None,
) -> SymbolDirectorySnapshot:
    parse_results = tuple(parse_nasdaq_symbol_directory_file(path) for path in paths)
    return _snapshot_from_parse_results(parse_results, imported_at=imported_at)


def save_symbol_directory_snapshot(
    snapshot: SymbolDirectorySnapshot,
    *,
    path: Path | str = DEFAULT_SYMBOL_DIRECTORY_SNAPSHOT_PATH,
) -> None:
    """Persist only normalized app-owned symbol records and safe metadata."""

    if not snapshot.records:
        raise SymbolDirectoryPersistenceError("symbol directory snapshot persistence failed")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": _SNAPSHOT_VERSION,
        "source_label": snapshot.source_label,
        "as_of_label": snapshot.as_of_label,
        "imported_at": snapshot.imported_at.isoformat(),
        "records": [
            {
                "symbol": record.symbol,
                "name": record.name,
                "asset_class": record.asset_class,
                "exchange": record.exchange,
                "region": record.region,
                "currency": record.currency,
                "is_supported": record.is_supported,
                "is_test_issue": record.is_test_issue,
            }
            for record in snapshot.records
        ],
    }
    try:
        tmp_path = target.with_suffix(target.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        tmp_path.replace(target)
    except Exception as exc:
        raise SymbolDirectoryPersistenceError("symbol directory snapshot persistence failed") from exc


def load_symbol_directory_snapshot(
    *,
    path: Path | str = DEFAULT_SYMBOL_DIRECTORY_SNAPSHOT_PATH,
) -> SymbolDirectorySnapshot | None:
    """Load a normalized snapshot, returning None for missing or malformed data."""

    source = Path(path)
    if not source.exists():
        return None
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        return _snapshot_from_payload(payload)
    except Exception:
        return None


def restore_active_symbol_directory_snapshot(
    *,
    path: Path | str = DEFAULT_SYMBOL_DIRECTORY_SNAPSHOT_PATH,
    store: SymbolDirectorySnapshotStore = GLOBAL_SYMBOL_DIRECTORY_STORE,
) -> SymbolDirectorySnapshot | None:
    snapshot = load_symbol_directory_snapshot(path=path)
    if snapshot is None:
        return None
    try:
        store.activate(snapshot)
    except Exception:
        return None
    return snapshot


def refresh_nasdaq_symbol_directory_snapshot(
    *,
    fetch_text: Callable[[str], str] | None = None,
    store: SymbolDirectorySnapshotStore = GLOBAL_SYMBOL_DIRECTORY_STORE,
    sources: Iterable[NasdaqSymbolDirectorySource] = DEFAULT_NASDAQ_SYMBOL_DIRECTORY_SOURCES,
    imported_at: datetime | None = None,
) -> SymbolDirectorySnapshot:
    """Fetch, parse, validate, and activate a last-good Nasdaq directory snapshot."""

    try:
        snapshot = build_nasdaq_symbol_directory_snapshot(
            fetch_text=fetch_text,
            sources=sources,
            imported_at=imported_at,
        )
        store.activate(snapshot)
        return snapshot
    except Exception as exc:
        raise SymbolDirectoryRefreshError("Nasdaq symbol directory refresh failed; last good snapshot was preserved") from exc


def manual_refresh_nasdaq_symbol_directory_snapshot(
    *,
    fetch_text: Callable[[str], str] | None = None,
    store: SymbolDirectorySnapshotStore = GLOBAL_SYMBOL_DIRECTORY_STORE,
    imported_at: datetime | None = None,
) -> SymbolDirectorySnapshot:
    """Manual refresh entrypoint for local demo/debug use."""

    return refresh_nasdaq_symbol_directory_snapshot(fetch_text=fetch_text, store=store, imported_at=imported_at)


def build_nasdaq_symbol_directory_snapshot(
    *,
    fetch_text: Callable[[str], str] | None = None,
    sources: Iterable[NasdaqSymbolDirectorySource] = DEFAULT_NASDAQ_SYMBOL_DIRECTORY_SOURCES,
    imported_at: datetime | None = None,
) -> SymbolDirectorySnapshot:
    fetch = fetch_text or fetch_public_text_url
    parse_results = tuple(parse_nasdaq_symbol_directory_text(fetch(source.url)) for source in sources)
    return _snapshot_from_parse_results(parse_results, imported_at=imported_at)


def refresh_and_persist_nasdaq_symbol_directory_snapshot(
    *,
    fetch_text: Callable[[str], str] | None = None,
    store: SymbolDirectorySnapshotStore = GLOBAL_SYMBOL_DIRECTORY_STORE,
    sources: Iterable[NasdaqSymbolDirectorySource] = DEFAULT_NASDAQ_SYMBOL_DIRECTORY_SOURCES,
    snapshot_path: Path | str = DEFAULT_SYMBOL_DIRECTORY_SNAPSHOT_PATH,
    imported_at: datetime | None = None,
) -> SymbolDirectorySnapshot:
    """Refresh and persist a normalized snapshot, activating only after full success."""

    try:
        snapshot = build_nasdaq_symbol_directory_snapshot(
            fetch_text=fetch_text,
            sources=sources,
            imported_at=imported_at,
        )
        save_symbol_directory_snapshot(snapshot, path=snapshot_path)
        store.activate(snapshot)
        return snapshot
    except Exception as exc:
        raise SymbolDirectoryRefreshError("Nasdaq symbol directory refresh failed; last good snapshot was preserved") from exc


def refresh_and_persist_symbol_directory_snapshot_if_due(
    *,
    max_age: timedelta = timedelta(days=1),
    fetch_text: Callable[[str], str] | None = None,
    store: SymbolDirectorySnapshotStore = GLOBAL_SYMBOL_DIRECTORY_STORE,
    sources: Iterable[NasdaqSymbolDirectorySource] = DEFAULT_NASDAQ_SYMBOL_DIRECTORY_SOURCES,
    snapshot_path: Path | str = DEFAULT_SYMBOL_DIRECTORY_SNAPSHOT_PATH,
    imported_at: datetime | None = None,
    now: Callable[[], datetime] | None = None,
) -> SymbolDirectorySnapshot | None:
    """Restore or refresh the local-demo directory without weakening last-good fallback."""

    active = store.active_snapshot or restore_active_symbol_directory_snapshot(path=snapshot_path, store=store)
    current = now() if now is not None else datetime.now(UTC)
    if active is not None and current - active.imported_at < max_age:
        return active
    return refresh_and_persist_nasdaq_symbol_directory_snapshot(
        fetch_text=fetch_text,
        store=store,
        sources=sources,
        snapshot_path=snapshot_path,
        imported_at=imported_at,
    )


def run_symbol_directory_startup_refresh_if_enabled() -> None:
    """Optional Docker/local-demo startup hook; never raises into app startup."""

    enabled = os.environ.get("SYMBOL_DIRECTORY_REFRESH_ON_STARTUP", "").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return
    try:
        refresh_and_persist_symbol_directory_snapshot_if_due()
    except SymbolDirectoryRefreshError:
        restore_active_symbol_directory_snapshot()


def manual_refresh_and_persist_nasdaq_symbol_directory_snapshot(
    *,
    fetch_text: Callable[[str], str] | None = None,
    store: SymbolDirectorySnapshotStore = GLOBAL_SYMBOL_DIRECTORY_STORE,
    snapshot_path: Path | str = DEFAULT_SYMBOL_DIRECTORY_SNAPSHOT_PATH,
    imported_at: datetime | None = None,
) -> SymbolDirectorySnapshot:
    """Manual local-demo refresh entrypoint that also persists the last-good snapshot."""

    return refresh_and_persist_nasdaq_symbol_directory_snapshot(
        fetch_text=fetch_text,
        store=store,
        snapshot_path=snapshot_path,
        imported_at=imported_at,
    )


def fetch_public_text_url(url: str, *, timeout_seconds: int = 15) -> str:
    request = Request(url, headers={"User-Agent": "portfolio-options-agent-symbol-directory/0.1"})
    with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310 - explicit manual/scheduled public file fetch
        return response.read().decode("utf-8", errors="replace")


def _snapshot_from_parse_results(
    parse_results: Iterable[SymbolDirectoryParseResult],
    *,
    imported_at: datetime | None,
) -> SymbolDirectorySnapshot:
    imported = imported_at or datetime.now(UTC)
    records: dict[str, SymbolRecord] = {}
    as_of_labels = []
    for result in parse_results:
        as_of_labels.append(result.as_of_label)
        for record in result.records:
            existing = records.get(record.symbol)
            if existing is None or _record_priority(record) > _record_priority(existing):
                records[record.symbol] = record
    if not records:
        raise ValueError("symbol directory snapshot did not contain normalized records")
    return SymbolDirectorySnapshot(
        records=tuple(record for _, record in sorted(records.items())),
        source_label=_NASDAQ_SOURCE_LABEL,
        as_of_label=_combined_as_of_label(as_of_labels, imported),
        imported_at=imported,
    )


def _snapshot_from_payload(payload: Any) -> SymbolDirectorySnapshot:
    if not isinstance(payload, dict) or payload.get("version") != _SNAPSHOT_VERSION:
        raise ValueError("invalid symbol directory snapshot version")
    records_payload = payload.get("records")
    if not isinstance(records_payload, list) or not records_payload:
        raise ValueError("invalid symbol directory snapshot records")
    records = tuple(_record_from_payload(item) for item in records_payload)
    return SymbolDirectorySnapshot(
        records=records,
        source_label=str(payload["source_label"]),
        as_of_label=str(payload["as_of_label"]),
        imported_at=datetime.fromisoformat(str(payload["imported_at"])),
    )


def _record_from_payload(payload: Any) -> SymbolRecord:
    if not isinstance(payload, dict):
        raise ValueError("invalid symbol directory record")
    return SymbolRecord(
        symbol=str(payload["symbol"]),
        name=str(payload["name"]),
        asset_class=str(payload["asset_class"]),
        exchange=str(payload["exchange"]),
        region=str(payload.get("region", "US")),
        currency=str(payload.get("currency", "USD")),
        is_supported=bool(payload.get("is_supported", False)),
        is_test_issue=bool(payload.get("is_test_issue", False)),
    )


def _combined_as_of_label(as_of_labels: list[str], imported_at: datetime) -> str:
    distinct = tuple(dict.fromkeys(label for label in as_of_labels if label))
    source_time = distinct[0] if len(distinct) == 1 else "Nasdaq Symbol Directory mixed file times"
    return f"{source_time}; imported {imported_at.isoformat()}"


def _parse_directory_row(row: list[str], columns: Mapping[str, int]) -> SymbolRecord | None:
    symbol = _field(row, columns, "symbol") or _field(row, columns, "act symbol")
    name = _field(row, columns, "security name")
    if not symbol or not name:
        return None
    exchange = _exchange_for_row(row, columns)
    is_test_issue = (_field(row, columns, "test issue") or "").upper() == "Y"
    is_etf = (_field(row, columns, "etf") or "").upper() == "Y"
    asset_class = _asset_class(name=name, is_etf=is_etf)
    try:
        return SymbolRecord(
            symbol=symbol,
            name=_clean_security_name(name),
            asset_class=asset_class,
            exchange=exchange,
            is_supported=not is_test_issue and asset_class in {"stock", "etf", "adr"},
            is_test_issue=is_test_issue,
        )
    except ValueError:
        return None


def _field(row: list[str], columns: Mapping[str, int], name: str) -> str | None:
    index = columns.get(name)
    if index is None or index >= len(row):
        return None
    return row[index].strip()


def _exchange_for_row(row: list[str], columns: Mapping[str, int]) -> str:
    exchange_code = (_field(row, columns, "exchange") or _field(row, columns, "listing exchange") or "").upper()
    if exchange_code:
        return _OTHER_LISTED_EXCHANGES.get(exchange_code, exchange_code)
    return _NASDAQ_EXCHANGE


def _asset_class(*, name: str, is_etf: bool) -> str:
    lowered = name.lower()
    if is_etf:
        return "etf"
    if " adr" in lowered or "american depositary" in lowered or "sponsored adr" in lowered:
        return "adr"
    return "stock"


def _clean_security_name(name: str) -> str:
    return name.replace(" - Common Stock", "").replace(" Common Stock", "").strip()


def _record_priority(record: SymbolRecord) -> int:
    if record.is_supported and not record.is_test_issue and record.asset_class in {"stock", "etf", "adr"}:
        return 2
    if record.is_supported and not record.is_test_issue:
        return 1
    return 0
