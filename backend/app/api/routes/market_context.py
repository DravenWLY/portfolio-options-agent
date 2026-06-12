from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.schemas.market_mood import MarketMoodDetailRead, MarketMoodRead, MarketMoodRefreshStatusRead
from app.services.market_mood import (
    MarketMoodRefreshError,
    MarketMoodRefreshResult,
    MarketMoodService,
    MarketMoodSnapshot,
    build_cnn_market_mood_refresh_runner,
)

router = APIRouter(prefix="/market-context", tags=["market-context"])


def get_market_mood_service() -> MarketMoodService:
    return MarketMoodService()


def get_market_mood_refresh_runner() -> Callable[[], MarketMoodRefreshResult]:
    return build_cnn_market_mood_refresh_runner()


@router.get("/market-mood", response_model=MarketMoodRead)
def get_market_mood(
    service: MarketMoodService = Depends(get_market_mood_service),
) -> MarketMoodRead:
    """Return broad market sentiment context for display only."""

    return service.get_market_mood()


@router.get("/market-mood/detail", response_model=MarketMoodDetailRead)
def get_market_mood_detail(
    service: MarketMoodService = Depends(get_market_mood_service),
) -> MarketMoodDetailRead:
    """Return full Market Mood detail context for display only."""

    return service.get_market_mood_detail()


@router.post("/market-mood/refresh", response_model=MarketMoodRefreshStatusRead)
def refresh_market_mood(
    refresh_runner: Callable[[], MarketMoodRefreshResult | MarketMoodSnapshot] = Depends(get_market_mood_refresh_runner),
) -> MarketMoodRefreshStatusRead:
    """Run an explicit internal-demo Market Mood refresh and return sanitized status."""

    try:
        result = refresh_runner()
    except MarketMoodRefreshError:
        checked_at = datetime.now(UTC)
        return MarketMoodRefreshStatusRead(
            status="failed",
            data_mode="unavailable",
            source_label="Market Mood unavailable",
            generated_at=None,
            updated_at_utc=None,
            source_changed=None,
            last_checked_at_utc=checked_at,
            last_checked_at_label=_checked_label(checked_at),
            record_count=0,
            message="Market Mood refresh failed; last good snapshot was preserved.",
        )
    if isinstance(result, MarketMoodRefreshResult):
        snapshot = result.snapshot
        return MarketMoodRefreshStatusRead(
            status=result.status,
            data_mode=snapshot.data_mode,
            source_label=snapshot.source_label,
            generated_at=snapshot.generated_at,
            updated_at_utc=snapshot.updated_at_utc,
            source_changed=result.source_changed,
            last_checked_at_utc=result.last_checked_at_utc,
            last_checked_at_label=_checked_label(result.last_checked_at_utc),
            record_count=len(snapshot.trend_series),
            message=result.message,
        )
    snapshot = result
    checked_at = datetime.now(UTC)
    return MarketMoodRefreshStatusRead(
        status="refreshed",
        data_mode=snapshot.data_mode,
        source_label=snapshot.source_label,
        generated_at=snapshot.generated_at,
        updated_at_utc=snapshot.updated_at_utc,
        source_changed=True,
        last_checked_at_utc=checked_at,
        last_checked_at_label=_checked_label(checked_at),
        record_count=len(snapshot.trend_series),
        message="Market Mood refresh completed.",
    )


def _checked_label(value: datetime) -> str:
    checked = value.astimezone(UTC)
    return checked.strftime("%Y-%m-%d %H:%M UTC")
