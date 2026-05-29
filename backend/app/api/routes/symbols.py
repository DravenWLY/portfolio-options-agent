from collections.abc import Callable

from fastapi import APIRouter, Depends, Query

from app.schemas.symbols import SymbolDirectoryRefreshStatusRead, SymbolSearchRead, SymbolValidationRead
from app.services.symbol_directory import (
    SymbolDirectoryRefreshError,
    SymbolDirectorySnapshot,
    refresh_and_persist_nasdaq_symbol_directory_snapshot,
)
from app.services.symbols import SymbolService

router = APIRouter(prefix="/symbols", tags=["symbols"])


def get_symbol_service() -> SymbolService:
    return SymbolService()


def get_symbol_directory_refresh_runner() -> Callable[[], SymbolDirectorySnapshot]:
    return refresh_and_persist_nasdaq_symbol_directory_snapshot


@router.get("/search", response_model=SymbolSearchRead)
def search_symbols(
    q: str = Query(default="", max_length=20),
    limit: int = Query(default=6, ge=1, le=25),
    service: SymbolService = Depends(get_symbol_service),
) -> SymbolSearchRead:
    """Return deterministic strict-prefix symbol suggestions."""

    return service.search(q, limit=limit)


@router.get("/validate", response_model=SymbolValidationRead)
def validate_symbol(
    symbol: str = Query(..., min_length=1, max_length=20),
    service: SymbolService = Depends(get_symbol_service),
) -> SymbolValidationRead:
    """Validate an exact normalized symbol against the app-owned reference."""

    return service.validate(symbol)


@router.post("/directory/refresh", response_model=SymbolDirectoryRefreshStatusRead)
def refresh_symbol_directory(
    refresh_runner: Callable[[], SymbolDirectorySnapshot] = Depends(get_symbol_directory_refresh_runner),
) -> SymbolDirectoryRefreshStatusRead:
    """Run an opt-in local symbol-directory refresh and return sanitized status."""

    try:
        snapshot = refresh_runner()
    except SymbolDirectoryRefreshError:
        return SymbolDirectoryRefreshStatusRead(
            status="failed",
            data_mode="unavailable",
            source_label="Symbol lookup unavailable",
            as_of_label="Unavailable",
            imported_at=None,
            record_count=0,
            message="Symbol directory refresh failed; last good snapshot was preserved.",
        )
    return SymbolDirectoryRefreshStatusRead(
        status="refreshed",
        data_mode="provider_reference",
        source_label=snapshot.source_label,
        as_of_label=snapshot.as_of_label,
        imported_at=snapshot.imported_at,
        record_count=len(snapshot.records),
        message="Symbol directory refresh completed.",
    )
