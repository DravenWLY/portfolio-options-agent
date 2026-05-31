from collections.abc import Callable
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.economic_calendar import EconomicCalendarEventListRead, EconomicCalendarRefreshStatusRead
from app.services.economic_calendar import (
    EconomicCalendarRefreshError,
    EconomicCalendarService,
    EconomicCalendarSnapshot,
    build_fmp_economic_calendar_refresh_runner_from_environment,
    resolve_economic_calendar_window,
)

router = APIRouter(prefix="/economic-calendar", tags=["economic-calendar"])


def get_economic_calendar_service() -> EconomicCalendarService:
    return EconomicCalendarService()


def get_economic_calendar_refresh_runner() -> Callable[[], EconomicCalendarSnapshot]:
    return build_fmp_economic_calendar_refresh_runner_from_environment()


def get_economic_calendar_current_date() -> date:
    return datetime.now(UTC).date()


@router.get("/events", response_model=EconomicCalendarEventListRead)
def list_economic_calendar_events(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    current_date: date = Depends(get_economic_calendar_current_date),
    service: EconomicCalendarService = Depends(get_economic_calendar_service),
) -> EconomicCalendarEventListRead:
    """Return public economic-calendar awareness events."""

    try:
        window_start, window_end = resolve_economic_calendar_window(
            start_date_text=start_date,
            end_date_text=end_date,
            current_date=current_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return service.list_events(window_start=window_start, window_end=window_end)


@router.post("/refresh", response_model=EconomicCalendarRefreshStatusRead)
def refresh_economic_calendar(
    refresh_runner: Callable[[], EconomicCalendarSnapshot] = Depends(get_economic_calendar_refresh_runner),
) -> EconomicCalendarRefreshStatusRead:
    """Run an opt-in local economic-calendar refresh and return sanitized status."""

    try:
        snapshot = refresh_runner()
    except EconomicCalendarRefreshError:
        return EconomicCalendarRefreshStatusRead(
            status="failed",
            data_mode="unavailable",
            source_label="Economic calendar unavailable",
            as_of_label="Unavailable",
            imported_at=None,
            record_count=0,
            message="Economic calendar refresh failed; last good snapshot was preserved.",
        )
    return EconomicCalendarRefreshStatusRead(
        status="refreshed",
        data_mode=snapshot.data_mode,
        source_label=snapshot.source_label,
        as_of_label=snapshot.as_of_label,
        imported_at=snapshot.imported_at,
        record_count=len(snapshot.records),
        message="Economic calendar refresh completed.",
    )
