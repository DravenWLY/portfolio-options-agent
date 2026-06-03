"""Market Mood contracts, fixtures, adapter, and normalized cache helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from app.schemas.market_mood import (
    MarketMoodComparisonRead,
    MarketMoodComponentRead,
    MarketMoodRead,
    MarketMoodTrendPointRead,
)


_SNAPSHOT_VERSION = 1
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MARKET_MOOD_SNAPSHOT_PATH = _BACKEND_ROOT / "cache" / "market_mood_snapshot.json"

SOURCE_LABEL = "CNN-derived Fear & Greed"
SOURCE_DETAIL_LABEL = "Latest available snapshot"
SOURCE_RIGHTS_NOTICE = "Not affiliated with CNN. Internal demo only pending source/rights review."
LIMITATIONS = (
    "Broad market sentiment context only. Not a trading signal.",
    "Internal demo only pending source/rights review.",
    "Not an actionability input, risk-rule input, market timing tool, screener, or instruction.",
)
SYNTHETIC_SOURCE_DETAIL_LABEL = "Synthetic fixture · not provider data"
UNAVAILABLE_SOURCE_LABEL = "Market Mood unavailable"
UNAVAILABLE_SOURCE_DETAIL_LABEL = "Unavailable"
FRESHNESS_MAX_AGE = timedelta(hours=24)

OVERALL_COMPONENT_KEY = "overall_fear_greed_index"
COMPONENT_DEFINITIONS = (
    (OVERALL_COMPONENT_KEY, "Overall Fear & Greed Index"),
    ("market_momentum", "Market Momentum"),
    ("stock_price_strength", "Stock Price Strength"),
    ("stock_price_breadth", "Stock Price Breadth"),
    ("put_call_options", "Put/Call Options"),
    ("market_volatility", "Market Volatility"),
    ("safe_haven_demand", "Safe Haven Demand"),
    ("junk_bond_demand", "Junk Bond Demand"),
)
DETAIL_COMPONENT_KEYS = tuple(key for key, _label in COMPONENT_DEFINITIONS if key != OVERALL_COMPONENT_KEY)


class MarketMoodRefreshError(RuntimeError):
    """Sanitized Market Mood refresh error."""


class MarketMoodPersistenceError(RuntimeError):
    """Sanitized Market Mood snapshot persistence error."""


class MarketMoodClient(Protocol):
    def fetch_market_mood(self) -> Mapping[str, Any]:
        """Fetch provider-shaped Market Mood data through an injected boundary."""


class MarketMoodProvider(Protocol):
    def snapshot(self) -> "MarketMoodSnapshot":
        """Return a normalized Market Mood snapshot."""


@dataclass(frozen=True)
class MarketMoodPoint:
    day: date
    score: float | None
    rating: str


@dataclass(frozen=True)
class MarketMoodComponent:
    component_key: str
    display_name: str
    score: float | None
    rating: str


@dataclass(frozen=True)
class MarketMoodSnapshot:
    data_mode: str
    source_label: str
    source_detail_label: str
    source_rights_notice: str
    generated_at: datetime
    updated_at_utc: datetime | None
    trend_series: tuple[MarketMoodPoint, ...]
    components: tuple[MarketMoodComponent, ...]
    caveat_codes: tuple[str, ...]
    limitations: tuple[str, ...]
    status_message: str | None = None

    @property
    def score(self) -> float | None:
        if not self.trend_series:
            return None
        return self.trend_series[-1].score

    @property
    def rating(self) -> str:
        if not self.trend_series:
            return "unknown"
        return self.trend_series[-1].rating


class MarketMoodSnapshotStore:
    """In-memory last-good Market Mood snapshot boundary."""

    def __init__(self) -> None:
        self._active_snapshot: MarketMoodSnapshot | None = None

    @property
    def active_snapshot(self) -> MarketMoodSnapshot | None:
        return self._active_snapshot

    def activate(self, snapshot: MarketMoodSnapshot) -> None:
        self._active_snapshot = snapshot

    def clear(self) -> None:
        self._active_snapshot = None


GLOBAL_MARKET_MOOD_STORE = MarketMoodSnapshotStore()
_AUTO_RESTORE_ENABLED = True


class SyntheticMarketMoodProvider:
    """Deterministic fixture provider for offline contract tests and dashboard design."""

    def __init__(self, *, generated_at: datetime | None = None) -> None:
        self._generated_at = generated_at

    def snapshot(self) -> MarketMoodSnapshot:
        generated = self._generated_at or datetime.now(UTC)
        points = (
            MarketMoodPoint(date(2025, 6, 2), 42.0, _rating_from_score(42.0)),
            MarketMoodPoint(date(2026, 5, 2), 49.0, _rating_from_score(49.0)),
            MarketMoodPoint(date(2026, 5, 26), 53.0, _rating_from_score(53.0)),
            MarketMoodPoint(date(2026, 6, 2), 57.0, _rating_from_score(57.0)),
        )
        return MarketMoodSnapshot(
            data_mode="synthetic",
            source_label=SOURCE_LABEL,
            source_detail_label=SYNTHETIC_SOURCE_DETAIL_LABEL,
            source_rights_notice=SOURCE_RIGHTS_NOTICE,
            generated_at=generated,
            updated_at_utc=generated,
            trend_series=points,
            components=_synthetic_components(),
            caveat_codes=("synthetic_fixture", "internal_demo_source_review_pending"),
            limitations=LIMITATIONS,
            status_message="Synthetic Market Mood fixture.",
        )


class SnapshotMarketMoodProvider:
    def __init__(self, snapshot: MarketMoodSnapshot) -> None:
        self._snapshot = snapshot

    def snapshot(self) -> MarketMoodSnapshot:
        return self._snapshot


class CnnDerivedMarketMoodProvider:
    """Normalize provider-shaped Fear & Greed payloads through an injected client."""

    def __init__(self, client: MarketMoodClient, *, generated_at: datetime | None = None) -> None:
        self._client = client
        self._generated_at = generated_at

    def snapshot(self) -> MarketMoodSnapshot:
        try:
            payload = self._client.fetch_market_mood()
            snapshot = _snapshot_from_provider_payload(payload, generated_at=self._generated_at or datetime.now(UTC))
        except Exception:
            raise MarketMoodRefreshError("market mood refresh failed; last good snapshot was preserved") from None
        if not snapshot.trend_series or len(snapshot.components) != len(DETAIL_COMPONENT_KEYS):
            raise MarketMoodRefreshError("market mood refresh failed; last good snapshot was preserved") from None
        return snapshot


class MarketMoodService:
    def __init__(self, provider: MarketMoodProvider | None = None) -> None:
        self._provider = provider or default_market_mood_provider()

    def get_market_mood(self, *, current_time: datetime | None = None) -> MarketMoodRead:
        try:
            snapshot = self._provider.snapshot()
        except Exception:
            return unavailable_market_mood_read(current_time=current_time)
        return read_from_snapshot(snapshot, current_time=current_time)


def default_market_mood_provider() -> MarketMoodProvider:
    snapshot = get_active_market_mood_snapshot()
    if snapshot is not None:
        return SnapshotMarketMoodProvider(snapshot)
    return SyntheticMarketMoodProvider()


def get_active_market_mood_snapshot() -> MarketMoodSnapshot | None:
    if _AUTO_RESTORE_ENABLED and GLOBAL_MARKET_MOOD_STORE.active_snapshot is None:
        restore_active_market_mood_snapshot()
    return GLOBAL_MARKET_MOOD_STORE.active_snapshot


def clear_active_market_mood_snapshot(*, disable_auto_restore: bool = False) -> None:
    GLOBAL_MARKET_MOOD_STORE.clear()
    set_market_mood_auto_restore_enabled(not disable_auto_restore)


def set_market_mood_auto_restore_enabled(enabled: bool) -> None:
    global _AUTO_RESTORE_ENABLED
    _AUTO_RESTORE_ENABLED = enabled


def read_from_snapshot(snapshot: MarketMoodSnapshot, *, current_time: datetime | None = None) -> MarketMoodRead:
    current = current_time or datetime.now(UTC)
    freshness_status, freshness_label = _freshness(snapshot, current_time=current)
    score = snapshot.score
    rating = _normalize_rating(snapshot.rating, score=score)
    return MarketMoodRead(
        data_mode=snapshot.data_mode,
        source_label=snapshot.source_label,
        source_detail_label=snapshot.source_detail_label,
        source_rights_notice=snapshot.source_rights_notice,
        generated_at=snapshot.generated_at,
        updated_at_utc=snapshot.updated_at_utc,
        updated_at_label=_updated_label(snapshot.updated_at_utc),
        freshness_status=freshness_status,
        freshness_label=freshness_label,
        is_trading_signal=False,
        is_actionability_input=False,
        is_risk_rule_input=False,
        score=score,
        score_label=_score_label(score),
        rating=rating,
        rating_label=_rating_label(rating),
        trend_series=tuple(_trend_point_read(point) for point in snapshot.trend_series),
        comparisons=_comparisons(snapshot.trend_series),
        components=tuple(_component_read(component) for component in snapshot.components),
        caveat_codes=snapshot.caveat_codes,
        limitations=snapshot.limitations,
        status_message=snapshot.status_message,
    )


def unavailable_market_mood_read(*, current_time: datetime | None = None) -> MarketMoodRead:
    generated = current_time or datetime.now(UTC)
    return MarketMoodRead(
        data_mode="unavailable",
        source_label=UNAVAILABLE_SOURCE_LABEL,
        source_detail_label=UNAVAILABLE_SOURCE_DETAIL_LABEL,
        source_rights_notice=SOURCE_RIGHTS_NOTICE,
        generated_at=generated,
        updated_at_utc=None,
        updated_at_label=None,
        freshness_status="unavailable",
        freshness_label="Market Mood unavailable.",
        is_trading_signal=False,
        is_actionability_input=False,
        is_risk_rule_input=False,
        score=None,
        score_label=None,
        rating="unknown",
        rating_label="Unknown",
        trend_series=(),
        comparisons=_empty_comparisons(),
        components=(),
        caveat_codes=("unavailable", "internal_demo_source_review_pending"),
        limitations=LIMITATIONS,
        status_message="Market Mood is temporarily unavailable.",
    )


def refresh_market_mood_unconfigured() -> MarketMoodSnapshot:
    """Default protected route runner. It is intentionally disabled until configured."""

    raise MarketMoodRefreshError("market mood refresh is not configured")


def refresh_and_persist_market_mood_snapshot(
    *,
    provider: MarketMoodProvider,
    store: MarketMoodSnapshotStore = GLOBAL_MARKET_MOOD_STORE,
    snapshot_path: Path | str = DEFAULT_MARKET_MOOD_SNAPSHOT_PATH,
) -> MarketMoodSnapshot:
    """Refresh, validate, persist, then activate a normalized Market Mood snapshot."""

    try:
        snapshot = provider.snapshot()
        _validate_snapshot(snapshot)
        save_market_mood_snapshot(snapshot, path=snapshot_path)
        store.activate(snapshot)
        return snapshot
    except Exception:
        pass
    raise MarketMoodRefreshError("market mood refresh failed; last good snapshot was preserved") from None


def save_market_mood_snapshot(
    snapshot: MarketMoodSnapshot,
    *,
    path: Path | str = DEFAULT_MARKET_MOOD_SNAPSHOT_PATH,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": _SNAPSHOT_VERSION,
        "data_mode": snapshot.data_mode,
        "source_label": snapshot.source_label,
        "source_detail_label": snapshot.source_detail_label,
        "source_rights_notice": snapshot.source_rights_notice,
        "generated_at": snapshot.generated_at.isoformat(),
        "updated_at_utc": snapshot.updated_at_utc.isoformat() if snapshot.updated_at_utc else None,
        "trend_series": [_point_payload(point) for point in snapshot.trend_series],
        "components": [_component_payload(component) for component in snapshot.components],
        "caveat_codes": list(snapshot.caveat_codes),
        "limitations": list(snapshot.limitations),
        "status_message": snapshot.status_message,
    }
    try:
        tmp_path = target.with_suffix(target.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        tmp_path.replace(target)
    except Exception:
        raise MarketMoodPersistenceError("market mood snapshot persistence failed") from None


def load_market_mood_snapshot(*, path: Path | str = DEFAULT_MARKET_MOOD_SNAPSHOT_PATH) -> MarketMoodSnapshot | None:
    source = Path(path)
    if not source.exists():
        return None
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        return _snapshot_from_payload(payload)
    except Exception:
        return None


def restore_active_market_mood_snapshot(
    *,
    path: Path | str = DEFAULT_MARKET_MOOD_SNAPSHOT_PATH,
    store: MarketMoodSnapshotStore = GLOBAL_MARKET_MOOD_STORE,
) -> MarketMoodSnapshot | None:
    snapshot = load_market_mood_snapshot(path=path)
    if snapshot is None:
        return None
    try:
        store.activate(snapshot)
    except Exception:
        return None
    return snapshot


def _snapshot_from_provider_payload(payload: Mapping[str, Any], *, generated_at: datetime) -> MarketMoodSnapshot:
    if not isinstance(payload, Mapping):
        raise ValueError("invalid market mood provider payload")
    overall = _nested_mapping(payload, ("fear_and_greed", "fearGreed", "fearGreedIndex", "overall")) or payload
    score = _safe_score(_first_value(overall, ("score", "value", "current_value", "currentValue")))
    rating = _normalize_rating(_first_string(overall, ("rating", "status", "classification")), score=score)
    updated = _parse_datetime(_first_value(overall, ("updated_at", "updatedAt", "timestamp", "lastUpdated")) or payload.get("updated_at"))
    trend_rows = _first_sequence(payload, ("trend", "history", "historical", "one_year_trend", "oneYearTrend"))
    trend_points = _trend_points_from_provider(trend_rows, current_score=score, current_rating=rating, updated_at=updated)
    components = _components_from_provider_payload(payload)
    return MarketMoodSnapshot(
        data_mode="provider_reference",
        source_label=SOURCE_LABEL,
        source_detail_label=SOURCE_DETAIL_LABEL,
        source_rights_notice=SOURCE_RIGHTS_NOTICE,
        generated_at=generated_at,
        updated_at_utc=updated,
        trend_series=trend_points,
        components=components,
        caveat_codes=("provider_reference", "internal_demo_source_review_pending"),
        limitations=LIMITATIONS,
        status_message="Latest available Market Mood snapshot.",
    )


def _trend_points_from_provider(
    rows: Sequence[Any],
    *,
    current_score: float | None,
    current_rating: str,
    updated_at: datetime | None,
) -> tuple[MarketMoodPoint, ...]:
    points = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        day = _parse_date(_first_value(row, ("date", "day", "x")))
        score = _safe_score(_first_value(row, ("score", "value", "y")))
        if day is None or score is None:
            continue
        points.append(MarketMoodPoint(day, score, _normalize_rating(_first_string(row, ("rating", "status")), score=score)))
    if not points and current_score is not None and updated_at is not None:
        points.append(MarketMoodPoint(updated_at.date(), current_score, current_rating))
    return tuple(sorted(points, key=lambda point: point.day))


def _components_from_provider_payload(payload: Mapping[str, Any]) -> tuple[MarketMoodComponent, ...]:
    component_source = _nested_mapping(payload, ("components", "indicators")) or payload
    components = []
    for key, display_name in COMPONENT_DEFINITIONS:
        if key == OVERALL_COMPONENT_KEY:
            continue
        source = _component_source(component_source, key)
        score = _safe_score(_first_value(source, ("score", "value", "current_value", "currentValue"))) if source else None
        rating = _normalize_rating(_first_string(source or {}, ("rating", "status", "classification")), score=score)
        components.append(MarketMoodComponent(key, display_name, score, rating))
    return tuple(components)


def _component_source(source: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    candidates = (key, key.replace("_", "-"), _camel_case(key), _pascal_case(key))
    for candidate in candidates:
        value = source.get(candidate)
        if isinstance(value, Mapping):
            return value
    return None


def _validate_snapshot(snapshot: MarketMoodSnapshot) -> None:
    read_from_snapshot(snapshot)


def _snapshot_from_payload(payload: Any) -> MarketMoodSnapshot:
    if not isinstance(payload, dict) or payload.get("version") != _SNAPSHOT_VERSION:
        raise ValueError("invalid market mood snapshot version")
    return MarketMoodSnapshot(
        data_mode=str(payload["data_mode"]),
        source_label=str(payload["source_label"]),
        source_detail_label=str(payload["source_detail_label"]),
        source_rights_notice=str(payload["source_rights_notice"]),
        generated_at=datetime.fromisoformat(str(payload["generated_at"])),
        updated_at_utc=_optional_datetime(payload.get("updated_at_utc")),
        trend_series=tuple(_point_from_payload(item) for item in payload.get("trend_series", ())),
        components=tuple(_component_from_payload(item) for item in payload.get("components", ())),
        caveat_codes=tuple(str(item) for item in payload.get("caveat_codes", ())),
        limitations=tuple(str(item) for item in payload.get("limitations", LIMITATIONS)),
        status_message=payload.get("status_message"),
    )


def _point_payload(point: MarketMoodPoint) -> dict[str, Any]:
    return {"date": point.day.isoformat(), "score": point.score, "rating": point.rating}


def _component_payload(component: MarketMoodComponent) -> dict[str, Any]:
    return {
        "component_key": component.component_key,
        "display_name": component.display_name,
        "score": component.score,
        "rating": component.rating,
    }


def _point_from_payload(payload: Any) -> MarketMoodPoint:
    if not isinstance(payload, Mapping):
        raise ValueError("invalid market mood trend point")
    day = date.fromisoformat(str(payload["date"]))
    score = _safe_score(payload.get("score"))
    return MarketMoodPoint(day, score, _normalize_rating(str(payload.get("rating", "unknown")), score=score))


def _component_from_payload(payload: Any) -> MarketMoodComponent:
    if not isinstance(payload, Mapping):
        raise ValueError("invalid market mood component")
    score = _safe_score(payload.get("score"))
    return MarketMoodComponent(
        str(payload["component_key"]),
        str(payload["display_name"]),
        score,
        _normalize_rating(str(payload.get("rating", "unknown")), score=score),
    )


def _synthetic_components() -> tuple[MarketMoodComponent, ...]:
    scores = {
        "market_momentum": 61.0,
        "stock_price_strength": 54.0,
        "stock_price_breadth": 51.0,
        "put_call_options": 48.0,
        "market_volatility": 58.0,
        "safe_haven_demand": 46.0,
        "junk_bond_demand": 59.0,
    }
    return tuple(
        MarketMoodComponent(key, label, scores[key], _rating_from_score(scores[key]))
        for key, label in COMPONENT_DEFINITIONS
        if key != OVERALL_COMPONENT_KEY
    )


def _trend_point_read(point: MarketMoodPoint) -> MarketMoodTrendPointRead:
    rating = _normalize_rating(point.rating, score=point.score)
    return MarketMoodTrendPointRead(
        date=point.day.isoformat(),
        score=point.score,
        score_label=_score_label(point.score),
        rating=rating,
        rating_label=_rating_label(rating),
    )


def _component_read(component: MarketMoodComponent) -> MarketMoodComponentRead:
    rating = _normalize_rating(component.rating, score=component.score)
    return MarketMoodComponentRead(
        component_key=component.component_key,
        display_name=component.display_name,
        score=component.score,
        score_label=_score_label(component.score),
        rating=rating,
        rating_label=_rating_label(rating),
    )


def _comparisons(points: Sequence[MarketMoodPoint]) -> tuple[MarketMoodComparisonRead, ...]:
    if not points or points[-1].score is None:
        return _empty_comparisons()
    latest = points[-1]
    windows = (("1w", 7), ("1m", 30), ("1y", 365))
    comparisons = []
    for window, days in windows:
        prior = _prior_point(points, latest.day - timedelta(days=days))
        if prior is None or prior.score is None:
            comparisons.append(
                MarketMoodComparisonRead(window=window, prior_score=None, prior_score_label=None, change_label=None, is_available=False)
            )
            continue
        change = latest.score - prior.score
        comparisons.append(
            MarketMoodComparisonRead(
                window=window,
                prior_score=prior.score,
                prior_score_label=_score_label(prior.score),
                change_label=f"{change:+.1f} points",
                is_available=True,
            )
        )
    return tuple(comparisons)


def _empty_comparisons() -> tuple[MarketMoodComparisonRead, ...]:
    return tuple(
        MarketMoodComparisonRead(window=window, prior_score=None, prior_score_label=None, change_label=None, is_available=False)
        for window in ("1w", "1m", "1y")
    )


def _prior_point(points: Sequence[MarketMoodPoint], target: date) -> MarketMoodPoint | None:
    candidates = [point for point in points if point.day <= target and point.score is not None]
    if not candidates:
        return None
    return candidates[-1]


def _freshness(snapshot: MarketMoodSnapshot, *, current_time: datetime) -> tuple[str, str]:
    if snapshot.data_mode == "unavailable" or snapshot.updated_at_utc is None:
        return ("unavailable", "Market Mood unavailable.")
    updated = _ensure_utc(snapshot.updated_at_utc)
    current = _ensure_utc(current_time)
    if current - updated > FRESHNESS_MAX_AGE:
        return ("stale", "Latest available Market Mood snapshot is stale.")
    return ("fresh", "Latest available Market Mood snapshot.")


def _updated_label(updated_at: datetime | None) -> str | None:
    if updated_at is None:
        return None
    return _ensure_utc(updated_at).isoformat().replace("+00:00", "Z")


def _safe_score(value: Any) -> float | None:
    if value is None:
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score != score or score < 0 or score > 100:
        return None
    return round(score, 2)


def _score_label(score: float | None) -> str | None:
    if score is None:
        return None
    if float(score).is_integer():
        return str(int(score))
    return f"{score:.1f}"


def _rating_from_score(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score <= 24:
        return "extreme_fear"
    if score <= 44:
        return "fear"
    if score <= 55:
        return "neutral"
    if score <= 75:
        return "greed"
    return "extreme_greed"


def _normalize_rating(value: str | None, *, score: float | None = None) -> str:
    text = (value or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "extreme_fear": "extreme_fear",
        "fear": "fear",
        "neutral": "neutral",
        "greed": "greed",
        "extreme_greed": "extreme_greed",
        "unknown": "unknown",
    }
    if text in aliases:
        return aliases[text]
    return _rating_from_score(score)


def _rating_label(rating: str) -> str:
    return {
        "extreme_fear": "Extreme fear",
        "fear": "Fear",
        "neutral": "Neutral",
        "greed": "Greed",
        "extreme_greed": "Extreme greed",
        "unknown": "Unknown",
    }.get(rating, "Unknown")


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000
        try:
            return datetime.fromtimestamp(timestamp, tz=UTC)
        except (OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return _ensure_utc(parsed)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return _parse_datetime(value)


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    parsed_datetime = _parse_datetime(value)
    if parsed_datetime is not None:
        return parsed_datetime.date()
    text = str(value).strip()
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _nested_mapping(payload: Mapping[str, Any], keys: Sequence[str]) -> Mapping[str, Any] | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, Mapping):
            return value
    return None


def _first_sequence(payload: Mapping[str, Any], keys: Sequence[str]) -> Sequence[Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return value
    return ()


def _first_value(payload: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _first_string(payload: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    value = _first_value(payload, keys)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _camel_case(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _pascal_case(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_"))
