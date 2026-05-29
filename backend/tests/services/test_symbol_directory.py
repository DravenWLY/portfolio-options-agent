from datetime import UTC, datetime, timedelta

import pytest

from app.services.symbol_directory import (
    NasdaqSymbolDirectorySource,
    DEFAULT_NASDAQ_SYMBOL_DIRECTORY_SOURCES,
    DEFAULT_SYMBOL_DIRECTORY_SNAPSHOT_PATH,
    SymbolDirectoryRefreshError,
    SymbolDirectoryRefreshJob,
    SymbolDirectorySnapshotStore,
    clear_active_symbol_directory_snapshot,
    import_nasdaq_symbol_directory_files,
    load_symbol_directory_snapshot,
    manual_refresh_and_persist_nasdaq_symbol_directory_snapshot,
    manual_refresh_nasdaq_symbol_directory_snapshot,
    parse_nasdaq_symbol_directory_file,
    refresh_and_persist_nasdaq_symbol_directory_snapshot,
    refresh_and_persist_symbol_directory_snapshot_if_due,
    refresh_nasdaq_symbol_directory_snapshot,
    run_symbol_directory_startup_refresh_if_enabled,
    restore_active_symbol_directory_snapshot,
    save_symbol_directory_snapshot,
)
from app.services.symbols import SymbolService


pytestmark = [pytest.mark.unit]

NOW = datetime(2026, 5, 28, 15, 0, tzinfo=UTC)

NASDAQ_LISTED_FIXTURE = """Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
NVDA|NVIDIA Corporation - Common Stock|Q|N|N|100|N|N
QQQ|Invesco QQQ Trust, Series 1|G|N|N|100|Y|N
TESTU|Synthetic Test Issue - Common Stock|Q|Y|N|100|N|N
File Creation Time: 0528202618:00|||||||
"""

OTHER_LISTED_FIXTURE = """ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
NOK|Nokia Corporation Sponsored ADR|N|NOK|N|100|N|NOK
SPY|SPDR S&P 500 ETF Trust|P|SPY|Y|100|N|SPY
BADT|Synthetic Other Test Issue|A|BADT|N|100|Y|BADT
File Creation Time: 0528202618:05|||||||
"""

NASDAQ_TRADED_FIXTURE = """Symbol|Security Name|Listing Exchange|Market Category|ETF|Round Lot Size|Test Issue|Financial Status|CQS Symbol|NASDAQ Symbol|NextShares
INTC|Intel Corporation - Common Stock|Q|Q|N|100|N|N|INTC|INTC|N
GLD|SPDR Gold Shares|P||Y|100|N||GLD|GLD|N
SLV|iShares Silver Trust|P||Y|100|N||SLV|SLV|N
BADT|Synthetic Traded Test Issue|A||N|100|Y||BADT|BADT|N
File Creation Time: 0528202618:10||||||||||
"""


@pytest.fixture(autouse=True)
def _clear_symbol_directory_snapshot():
    clear_active_symbol_directory_snapshot(disable_auto_restore=True)
    yield
    clear_active_symbol_directory_snapshot(disable_auto_restore=True)


def test_parse_nasdaqlisted_fixture_rows_and_footer(tmp_path) -> None:
    path = tmp_path / "nasdaqlisted.txt"
    path.write_text(NASDAQ_LISTED_FIXTURE, encoding="utf-8")

    parsed = parse_nasdaq_symbol_directory_file(path)

    by_symbol = {record.symbol: record for record in parsed.records}
    assert parsed.as_of_label == "Nasdaq Symbol Directory file time 0528202618:00|||||||"
    assert by_symbol["NVDA"].asset_class == "stock"
    assert by_symbol["NVDA"].exchange == "NASDAQ"
    assert by_symbol["QQQ"].asset_class == "etf"
    assert by_symbol["TESTU"].is_test_issue is True
    assert by_symbol["TESTU"].is_supported is False


def test_parse_otherlisted_fixture_rows_and_footer(tmp_path) -> None:
    path = tmp_path / "otherlisted.txt"
    path.write_text(OTHER_LISTED_FIXTURE, encoding="utf-8")

    parsed = parse_nasdaq_symbol_directory_file(path)

    by_symbol = {record.symbol: record for record in parsed.records}
    assert parsed.as_of_label == "Nasdaq Symbol Directory file time 0528202618:05|||||||"
    assert by_symbol["NOK"].asset_class == "adr"
    assert by_symbol["NOK"].exchange == "NYSE"
    assert by_symbol["SPY"].asset_class == "etf"
    assert by_symbol["SPY"].exchange == "NYSEARCA"
    assert by_symbol["BADT"].is_test_issue is True
    assert by_symbol["BADT"].is_supported is False


def test_parse_nasdaqtraded_fixture_covers_cross_market_symbols(tmp_path) -> None:
    path = tmp_path / "nasdaqtraded.txt"
    path.write_text(NASDAQ_TRADED_FIXTURE, encoding="utf-8")

    parsed = parse_nasdaq_symbol_directory_file(path)

    by_symbol = {record.symbol: record for record in parsed.records}
    assert parsed.as_of_label == "Nasdaq Symbol Directory file time 0528202618:10||||||||||"
    assert by_symbol["INTC"].exchange == "NASDAQ"
    assert by_symbol["INTC"].asset_class == "stock"
    assert by_symbol["GLD"].exchange == "NYSEARCA"
    assert by_symbol["GLD"].asset_class == "etf"
    assert by_symbol["SLV"].exchange == "NYSEARCA"
    assert by_symbol["SLV"].asset_class == "etf"
    assert by_symbol["BADT"].is_test_issue is True
    assert by_symbol["BADT"].is_supported is False


def test_default_sources_use_broad_nasdaq_traded_directory() -> None:
    assert [source.name for source in DEFAULT_NASDAQ_SYMBOL_DIRECTORY_SOURCES] == ["nasdaqtraded"]
    assert DEFAULT_NASDAQ_SYMBOL_DIRECTORY_SOURCES[0].url.endswith("/nasdaqtraded.txt")
    assert DEFAULT_SYMBOL_DIRECTORY_SNAPSHOT_PATH.parts[-3:] == ("backend", "cache", "symbol_directory_snapshot.json")


def test_imported_snapshot_becomes_default_symbol_provider(tmp_path) -> None:
    nasdaq_path = tmp_path / "nasdaqlisted.txt"
    other_path = tmp_path / "otherlisted.txt"
    nasdaq_path.write_text(NASDAQ_LISTED_FIXTURE, encoding="utf-8")
    other_path.write_text(OTHER_LISTED_FIXTURE, encoding="utf-8")
    snapshot = import_nasdaq_symbol_directory_files((nasdaq_path, other_path), imported_at=NOW)
    store = SymbolDirectorySnapshotStore()
    store.activate(snapshot)

    from app.services import symbol_directory

    symbol_directory.GLOBAL_SYMBOL_DIRECTORY_STORE.activate(snapshot)
    search = SymbolService().search("NOK")
    validation = SymbolService().validate("NOK")

    assert search.data_mode == "provider_reference"
    assert search.source_label == "Nasdaq Symbol Directory"
    assert "imported 2026-05-28T15:00:00+00:00" in search.as_of_label
    assert [item.symbol for item in search.items][0] == "NOK"
    assert validation.is_found is True
    assert validation.is_supported is True


def test_successful_refresh_replaces_active_snapshot() -> None:
    store = SymbolDirectorySnapshotStore()

    snapshot = refresh_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: NASDAQ_LISTED_FIXTURE if "nasdaq" in url else OTHER_LISTED_FIXTURE,
        store=store,
        sources=(
            NasdaqSymbolDirectorySource(name="nasdaqlisted", url="https://example.invalid/nasdaqlisted.txt"),
            NasdaqSymbolDirectorySource(name="otherlisted", url="https://example.invalid/otherlisted.txt"),
        ),
        imported_at=NOW,
    )

    assert store.active_snapshot is snapshot
    assert {record.symbol for record in snapshot.records} >= {"NVDA", "QQQ", "NOK", "SPY"}
    assert snapshot.source_label == "Nasdaq Symbol Directory"


def test_default_refresh_path_finds_intc_gld_and_slv() -> None:
    store = SymbolDirectorySnapshotStore()

    snapshot = refresh_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: NASDAQ_TRADED_FIXTURE,
        store=store,
        imported_at=NOW,
    )

    symbols = {record.symbol for record in snapshot.records}
    assert symbols >= {"INTC", "GLD", "SLV"}
    assert SymbolService().search("INTC").data_mode == "synthetic"
    store.activate(snapshot)
    from app.services import symbol_directory

    symbol_directory.GLOBAL_SYMBOL_DIRECTORY_STORE.activate(snapshot)
    assert [item.symbol for item in SymbolService().search("INTC").items] == ["INTC"]
    assert [item.symbol for item in SymbolService().search("GLD").items] == ["GLD"]


def test_failed_refresh_preserves_last_good_snapshot_and_sanitizes_error() -> None:
    store = SymbolDirectorySnapshotStore()
    last_good = refresh_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: NASDAQ_LISTED_FIXTURE,
        store=store,
        sources=(NasdaqSymbolDirectorySource(name="nasdaqlisted", url="https://example.invalid/nasdaqlisted.txt"),),
        imported_at=NOW,
    )

    def failing_fetch(_url: str) -> str:
        raise RuntimeError("raw_payload provider_account_id secret downloaded row")

    with pytest.raises(SymbolDirectoryRefreshError) as exc_info:
        refresh_nasdaq_symbol_directory_snapshot(
            fetch_text=failing_fetch,
            store=store,
            sources=(NasdaqSymbolDirectorySource(name="nasdaqlisted", url="https://example.invalid/nasdaqlisted.txt"),),
            imported_at=NOW + timedelta(hours=1),
        )

    assert store.active_snapshot is last_good
    rendered = str(exc_info.value).lower()
    assert "raw_payload" not in rendered
    assert "provider_account_id" not in rendered
    assert "secret" not in rendered


def test_manual_refresh_uses_same_importer_path() -> None:
    store = SymbolDirectorySnapshotStore()

    snapshot = manual_refresh_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: NASDAQ_LISTED_FIXTURE,
        store=store,
        imported_at=NOW,
    )

    assert store.active_snapshot is snapshot
    assert {record.symbol for record in snapshot.records} >= {"NVDA", "QQQ"}


def test_scheduled_refresh_is_disabled_by_default_and_does_not_fetch() -> None:
    calls = 0

    def refresh():
        nonlocal calls
        calls += 1
        raise AssertionError("refresh should not run while disabled")

    job = SymbolDirectoryRefreshJob(enabled=False, refresh=refresh)

    assert job.run_pending() is None
    assert calls == 0


def test_scheduled_refresh_runs_only_when_due() -> None:
    store = SymbolDirectorySnapshotStore()
    current = NOW

    def now() -> datetime:
        return current

    def refresh():
        return refresh_nasdaq_symbol_directory_snapshot(
            fetch_text=lambda url: NASDAQ_LISTED_FIXTURE,
            store=store,
            imported_at=current,
        )

    job = SymbolDirectoryRefreshJob(enabled=True, interval=timedelta(days=1), refresh=refresh, now=now)

    first = job.run_pending()
    second = job.run_pending()

    assert first is store.active_snapshot
    assert second is None


def test_symbol_directory_snapshot_save_load_round_trip(tmp_path) -> None:
    snapshot = refresh_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: NASDAQ_LISTED_FIXTURE,
        store=SymbolDirectorySnapshotStore(),
        sources=(NasdaqSymbolDirectorySource(name="nasdaqlisted", url="https://example.invalid/nasdaqlisted.txt"),),
        imported_at=NOW,
    )
    path = tmp_path / "symbol-directory.json"

    save_symbol_directory_snapshot(snapshot, path=path)
    loaded = load_symbol_directory_snapshot(path=path)

    assert loaded is not None
    assert loaded.source_label == "Nasdaq Symbol Directory"
    assert loaded.as_of_label == snapshot.as_of_label
    assert loaded.imported_at == NOW
    assert {record.symbol for record in loaded.records} >= {"NVDA", "QQQ"}
    rendered = path.read_text(encoding="utf-8").lower()
    assert "raw_payload" not in rendered
    assert "nasdaq symbol directory file time" in rendered


def test_restore_from_persisted_snapshot_after_restart_style_clear(tmp_path) -> None:
    snapshot = refresh_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: OTHER_LISTED_FIXTURE,
        store=SymbolDirectorySnapshotStore(),
        sources=(NasdaqSymbolDirectorySource(name="otherlisted", url="https://example.invalid/otherlisted.txt"),),
        imported_at=NOW,
    )
    path = tmp_path / "symbol-directory.json"
    save_symbol_directory_snapshot(snapshot, path=path)
    store = SymbolDirectorySnapshotStore()

    restored = restore_active_symbol_directory_snapshot(path=path, store=store)

    assert restored is not None
    assert store.active_snapshot is restored
    assert {record.symbol for record in restored.records} >= {"NOK", "SPY"}


def test_malformed_persisted_snapshot_falls_back_to_synthetic_provider(tmp_path) -> None:
    path = tmp_path / "symbol-directory.json"
    path.write_text('{"version": 1, "records": [{"raw_payload": "secret"}]}', encoding="utf-8")

    restored = restore_active_symbol_directory_snapshot(path=path)
    search = SymbolService().search("NV")

    assert restored is None
    assert search.data_mode == "synthetic"
    assert [item.symbol for item in search.items] == ["NVDA", "NVDL"]


def test_refresh_and_persist_activates_only_after_success(tmp_path) -> None:
    store = SymbolDirectorySnapshotStore()
    path = tmp_path / "symbol-directory.json"

    snapshot = refresh_and_persist_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: NASDAQ_LISTED_FIXTURE if "nasdaq" in url else OTHER_LISTED_FIXTURE,
        store=store,
        sources=(
            NasdaqSymbolDirectorySource(name="nasdaqlisted", url="https://example.invalid/nasdaqlisted.txt"),
            NasdaqSymbolDirectorySource(name="otherlisted", url="https://example.invalid/otherlisted.txt"),
        ),
        snapshot_path=path,
        imported_at=NOW,
    )
    loaded = load_symbol_directory_snapshot(path=path)

    assert store.active_snapshot is snapshot
    assert loaded is not None
    assert {record.symbol for record in loaded.records} >= {"NVDA", "NOK"}


def test_failed_refresh_and_persist_preserves_active_and_persisted_last_good(tmp_path) -> None:
    store = SymbolDirectorySnapshotStore()
    path = tmp_path / "symbol-directory.json"
    last_good = refresh_and_persist_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: NASDAQ_LISTED_FIXTURE,
        store=store,
        sources=(NasdaqSymbolDirectorySource(name="nasdaqlisted", url="https://example.invalid/nasdaqlisted.txt"),),
        snapshot_path=path,
        imported_at=NOW,
    )

    def failing_fetch(_url: str) -> str:
        raise RuntimeError("raw_payload provider_account_id secret downloaded row")

    with pytest.raises(SymbolDirectoryRefreshError):
        refresh_and_persist_nasdaq_symbol_directory_snapshot(
            fetch_text=failing_fetch,
            store=store,
            sources=(NasdaqSymbolDirectorySource(name="nasdaqlisted", url="https://example.invalid/nasdaqlisted.txt"),),
            snapshot_path=path,
            imported_at=NOW + timedelta(hours=1),
        )

    loaded = load_symbol_directory_snapshot(path=path)
    assert store.active_snapshot is last_good
    assert loaded is not None
    assert loaded.imported_at == NOW
    assert {record.symbol for record in loaded.records} >= {"NVDA", "QQQ"}


def test_manual_refresh_and_persist_uses_same_importer_path(tmp_path) -> None:
    store = SymbolDirectorySnapshotStore()
    path = tmp_path / "symbol-directory.json"

    snapshot = manual_refresh_and_persist_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: OTHER_LISTED_FIXTURE,
        store=store,
        snapshot_path=path,
        imported_at=NOW,
    )

    assert store.active_snapshot is snapshot
    assert load_symbol_directory_snapshot(path=path) is not None


def test_default_service_path_does_not_fetch_network(monkeypatch) -> None:
    from app.services import symbol_directory

    def fail_fetch(*_args, **_kwargs):
        raise AssertionError("default SymbolService path must not fetch")

    monkeypatch.setattr(symbol_directory, "fetch_public_text_url", fail_fetch)

    result = SymbolService().search("NV")

    assert result.data_mode == "synthetic"


def test_refresh_if_due_uses_persisted_snapshot_before_network(tmp_path) -> None:
    path = tmp_path / "symbol-directory.json"
    old = refresh_and_persist_nasdaq_symbol_directory_snapshot(
        fetch_text=lambda url: NASDAQ_TRADED_FIXTURE,
        store=SymbolDirectorySnapshotStore(),
        snapshot_path=path,
        imported_at=NOW,
    )
    store = SymbolDirectorySnapshotStore()

    restored = refresh_and_persist_symbol_directory_snapshot_if_due(
        store=store,
        snapshot_path=path,
        now=lambda: NOW + timedelta(hours=2),
        fetch_text=lambda _url: pytest.fail("fresh persisted snapshot should not fetch"),
    )

    assert restored is not None
    assert restored.imported_at == old.imported_at
    assert store.active_snapshot is restored


def test_startup_refresh_hook_is_disabled_unless_env_enabled(monkeypatch) -> None:
    monkeypatch.delenv("SYMBOL_DIRECTORY_REFRESH_ON_STARTUP", raising=False)
    from app.services import symbol_directory

    monkeypatch.setattr(
        symbol_directory,
        "refresh_and_persist_symbol_directory_snapshot_if_due",
        lambda: pytest.fail("startup refresh must be opt-in"),
    )

    run_symbol_directory_startup_refresh_if_enabled()
