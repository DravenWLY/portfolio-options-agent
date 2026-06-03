from collections.abc import Callable

from fastapi import APIRouter, Depends

from app.schemas.market_mood import MarketMoodRead, MarketMoodRefreshStatusRead
from app.services.market_mood import (
    MarketMoodRefreshError,
    MarketMoodService,
    MarketMoodSnapshot,
    refresh_market_mood_unconfigured,
)

router = APIRouter(prefix="/market-context", tags=["market-context"])


def get_market_mood_service() -> MarketMoodService:
    return MarketMoodService()


def get_market_mood_refresh_runner() -> Callable[[], MarketMoodSnapshot]:
    return refresh_market_mood_unconfigured


@router.get("/market-mood", response_model=MarketMoodRead)
def get_market_mood(
    service: MarketMoodService = Depends(get_market_mood_service),
) -> MarketMoodRead:
    """Return broad market sentiment context for display only."""

    return service.get_market_mood()


@router.post("/market-mood/refresh", response_model=MarketMoodRefreshStatusRead)
def refresh_market_mood(
    refresh_runner: Callable[[], MarketMoodSnapshot] = Depends(get_market_mood_refresh_runner),
) -> MarketMoodRefreshStatusRead:
    """Run an explicit internal-demo Market Mood refresh and return sanitized status."""

    try:
        snapshot = refresh_runner()
    except MarketMoodRefreshError:
        return MarketMoodRefreshStatusRead(
            status="failed",
            data_mode="unavailable",
            source_label="Market Mood unavailable",
            generated_at=None,
            updated_at_utc=None,
            record_count=0,
            message="Market Mood refresh failed; last good snapshot was preserved.",
        )
    return MarketMoodRefreshStatusRead(
        status="refreshed",
        data_mode=snapshot.data_mode,
        source_label=snapshot.source_label,
        generated_at=snapshot.generated_at,
        updated_at_utc=snapshot.updated_at_utc,
        record_count=len(snapshot.trend_series),
        message="Market Mood refresh completed.",
    )
