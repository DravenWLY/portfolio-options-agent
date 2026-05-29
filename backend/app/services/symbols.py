"""Provider-neutral symbol lookup service with an offline fallback provider."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol, Sequence

from app.schemas.symbols import SymbolSearchItemRead, SymbolSearchRead, SymbolValidationRead
from app.services.symbol_fixtures import OFFLINE_SYMBOL_FIXTURES


_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")
_SOURCE_LABEL = "Offline symbol fallback fixture"
_AS_OF_LABEL = "Offline fixture · not live market data"
_UNAVAILABLE_LABEL = "Symbol lookup unavailable"
_SUPPORTED_ASSET_CLASSES = {"stock", "etf", "adr"}
_MAX_SEARCH_RESULTS = 6


@dataclass(frozen=True)
class SymbolRecord:
    symbol: str
    name: str
    asset_class: str
    exchange: str
    region: str = "US"
    currency: str = "USD"
    is_supported: bool = True
    is_test_issue: bool = False

    def __post_init__(self) -> None:
        symbol = normalize_symbol_text(self.symbol)
        if not symbol or _SYMBOL_RE.fullmatch(symbol) is None:
            raise ValueError("symbol must be a normalized display-safe ticker")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "asset_class", self.asset_class.strip().lower())
        object.__setattr__(self, "exchange", self.exchange.strip().upper())
        object.__setattr__(self, "region", self.region.strip().upper())
        object.__setattr__(self, "currency", self.currency.strip().upper())


class SymbolProvider(Protocol):
    data_mode: str
    source_label: str
    as_of_label: str

    def list_symbols(self) -> Sequence[SymbolRecord]:
        """Return provider-owned symbol records without exposing raw payloads."""


class DemoSymbolProvider:
    """Small deterministic provider backed by offline fallback records."""

    data_mode = "synthetic"
    source_label = _SOURCE_LABEL
    as_of_label = _AS_OF_LABEL

    def __init__(self, records: Sequence[SymbolRecord] | None = None) -> None:
        self._records = tuple(records or _offline_symbol_records())

    def list_symbols(self) -> Sequence[SymbolRecord]:
        return self._records


class SymbolDirectorySnapshotProvider:
    """Provider wrapper for an already-normalized last-good directory snapshot."""

    data_mode = "provider_reference"

    def __init__(self, snapshot: object) -> None:
        self._snapshot = snapshot
        self.source_label = str(getattr(snapshot, "source_label", "Symbol directory"))
        self.as_of_label = str(getattr(snapshot, "as_of_label", "Symbol directory as-of unavailable"))

    def list_symbols(self) -> Sequence[SymbolRecord]:
        return tuple(getattr(self._snapshot, "records", ()))


class SymbolService:
    def __init__(self, provider: SymbolProvider | None = None) -> None:
        self._provider = provider or default_symbol_provider()

    def search(self, query: str, *, limit: int = _MAX_SEARCH_RESULTS) -> SymbolSearchRead:
        normalized = normalize_symbol_text(query)
        if not normalized:
            return self._search_response(
                query="",
                normalized_query="",
                items=(),
                message="",
                result_mode="empty",
                section_label="",
                no_match=False,
            )
        if _SYMBOL_RE.fullmatch(normalized) is None:
            return self._search_response(
                query=query.strip(),
                normalized_query=normalized,
                items=(),
                message="Symbol Not Found",
                result_mode="no_match",
                section_label="Symbol Not Found",
            )

        try:
            records = self._deduplicated_records()
        except Exception:
            return self._unavailable_search(query=query.strip(), normalized_query=normalized)

        matched = []
        for record in records.values():
            match_kind = _match_kind(record, normalized)
            if match_kind is None:
                continue
            matched.append((record, match_kind))
        matched.sort(key=lambda item: _search_sort_key(item[0], item[1]))

        items = tuple(
            _search_item(
                record,
                match_type=_public_match_type(match_kind),
                score_label=_score_label(match_kind),
                provider=self._provider,
            )
            for record, match_kind in matched[: max(1, min(limit, _MAX_SEARCH_RESULTS))]
        )

        return self._search_response(
            query=query.strip(),
            normalized_query=normalized,
            items=tuple(items),
            message="Symbol Not Found" if not items else "Search results",
            result_mode="no_match" if not items else "search",
            section_label="Symbol Not Found" if not items else "Search results",
        )

    def validate(self, symbol: str) -> SymbolValidationRead:
        normalized = normalize_symbol_text(symbol)
        if not normalized or _SYMBOL_RE.fullmatch(normalized) is None:
            return self._validation_not_found(symbol=symbol.strip(), normalized_symbol=normalized)

        try:
            record = self._deduplicated_records(include_unsupported=True).get(normalized)
        except Exception:
            return SymbolValidationRead(
                symbol=symbol.strip(),
                normalized_symbol=normalized,
                is_found=False,
                is_supported=False,
                asset_class="unknown",
                exchange=None,
                name=None,
                data_mode="unavailable",
                source_label=_UNAVAILABLE_LABEL,
                as_of_label="Unavailable",
                message="Symbol validation is temporarily unavailable.",
            )

        if record is None:
            return self._validation_not_found(symbol=symbol.strip(), normalized_symbol=normalized)

        supported = record.is_supported and not record.is_test_issue and record.asset_class in _SUPPORTED_ASSET_CLASSES
        return SymbolValidationRead(
            symbol=symbol.strip(),
            normalized_symbol=normalized,
            is_found=True,
            is_supported=supported,
            asset_class=record.asset_class,
            exchange=record.exchange,
            name=record.name,
            data_mode=self._provider.data_mode,
            source_label=self._provider.source_label,
            as_of_label=self._provider.as_of_label,
            message="Symbol is supported." if supported else "Symbol found but not supported for this workflow.",
        )

    def _search_response(
        self,
        *,
        query: str,
        normalized_query: str,
        items: tuple[SymbolSearchItemRead, ...],
        message: str,
        result_mode: str,
        section_label: str,
        no_match: bool | None = None,
    ) -> SymbolSearchRead:
        return SymbolSearchRead(
            query=query,
            normalized_query=normalized_query,
            data_mode=self._provider.data_mode,
            result_mode=result_mode,
            section_label=section_label,
            source_label=self._provider.source_label,
            as_of_label=self._provider.as_of_label,
            items=items,
            no_match=not items if no_match is None else no_match,
            message=message,
        )

    def _unavailable_search(self, *, query: str, normalized_query: str) -> SymbolSearchRead:
        return SymbolSearchRead(
            query=query,
            normalized_query=normalized_query,
            data_mode="unavailable",
            result_mode="unavailable",
            section_label="Symbol lookup unavailable",
            source_label=_UNAVAILABLE_LABEL,
            as_of_label="Unavailable",
            items=(),
            no_match=True,
            message="Symbol lookup is temporarily unavailable.",
        )

    def _validation_not_found(self, *, symbol: str, normalized_symbol: str) -> SymbolValidationRead:
        return SymbolValidationRead(
            symbol=symbol,
            normalized_symbol=normalized_symbol,
            is_found=False,
            is_supported=False,
            asset_class="unknown",
            exchange=None,
            name=None,
            data_mode=self._provider.data_mode,
            source_label=self._provider.source_label,
            as_of_label=self._provider.as_of_label,
            message="Symbol Not Found",
        )

    def _deduplicated_records(self, *, include_unsupported: bool = False) -> dict[str, SymbolRecord]:
        records: dict[str, SymbolRecord] = {}
        for record in self._provider.list_symbols():
            if not include_unsupported and not _is_search_visible(record):
                continue
            existing = records.get(record.symbol)
            if existing is None or _record_priority(record) > _record_priority(existing):
                records[record.symbol] = record
        return dict(sorted(records.items(), key=lambda item: item[0]))


def normalize_symbol_text(value: str) -> str:
    return value.strip().upper().replace(" ", "")


def default_symbol_provider() -> SymbolProvider:
    from app.services.symbol_directory import get_active_symbol_directory_snapshot

    snapshot = get_active_symbol_directory_snapshot()
    if snapshot is not None:
        return SymbolDirectorySnapshotProvider(snapshot)
    return DemoSymbolProvider()


def _record_priority(record: SymbolRecord) -> int:
    if record.is_supported and not record.is_test_issue and record.asset_class in _SUPPORTED_ASSET_CLASSES:
        return 2
    if record.is_supported and not record.is_test_issue:
        return 1
    return 0


def _is_search_visible(record: SymbolRecord) -> bool:
    return record.is_supported and not record.is_test_issue and record.asset_class in _SUPPORTED_ASSET_CLASSES


def _match_kind(record: SymbolRecord, normalized_query: str) -> str | None:
    if record.symbol == normalized_query:
        return "exact"
    if record.symbol.startswith(normalized_query):
        return "prefix"
    if normalized_query in record.symbol:
        return "symbol_contains"
    if len(normalized_query) >= 3 and normalized_query in normalize_symbol_text(record.name):
        return "name_contains"
    return None


def _search_sort_key(record: SymbolRecord, match_kind: str) -> tuple[int, int, int, str]:
    match_rank = {"exact": 0, "prefix": 1, "symbol_contains": 2, "name_contains": 3}[match_kind]
    asset_rank = {"stock": 0, "etf": 1, "adr": 2, "option": 3, "index": 4, "unknown": 5}.get(record.asset_class, 5)
    exchange_rank = {"NASDAQ": 0, "NYSE": 1, "NYSEARCA": 2, "OTC": 3, "CBOE": 4}.get(record.exchange, 9)
    return (match_rank, asset_rank, exchange_rank, record.symbol)


def _public_match_type(match_kind: str) -> str:
    return "contains" if match_kind in {"symbol_contains", "name_contains"} else match_kind


def _score_label(match_kind: str) -> str:
    return {
        "exact": "Exact symbol match",
        "prefix": "Symbol prefix match",
        "symbol_contains": "Symbol contains match",
        "name_contains": "Reference match",
    }[match_kind]


def _search_item(
    record: SymbolRecord,
    *,
    match_type: str,
    score_label: str,
    provider: SymbolProvider,
) -> SymbolSearchItemRead:
    return SymbolSearchItemRead(
        symbol=record.symbol,
        name=record.name,
        asset_class=record.asset_class,
        exchange=record.exchange,
        region=record.region,
        currency=record.currency,
        is_supported=record.is_supported,
        match_type=match_type,
        score_label=score_label,
        source_label=provider.source_label,
        as_of_label=provider.as_of_label,
    )


def _offline_symbol_records() -> tuple[SymbolRecord, ...]:
    return tuple(SymbolRecord(**row) for row in OFFLINE_SYMBOL_FIXTURES)
