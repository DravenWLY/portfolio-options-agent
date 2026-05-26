from datetime import UTC, datetime, timedelta

import pytest

from app.services.market_data.freshness import (
    DEFAULT_MAX_QUOTE_AGE_SECONDS,
    classify_quote_actionability,
    classify_quote_freshness,
    evaluate_quote_freshness,
)


pytestmark = [pytest.mark.unit]


def test_live_recent_quote_is_actionable_market_snapshot() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)

    decision = evaluate_quote_freshness(
        data_mode="live",
        quote_time=now - timedelta(seconds=30),
        received_at=now,
        now=now,
    )

    assert decision.freshness_scope == "market_quote"
    assert decision.freshness_status == "fresh"
    assert decision.actionability_status == "actionable_snapshot"
    assert decision.quote_age_seconds == 30


def test_delayed_manual_and_eod_quotes_are_analysis_only() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)

    delayed = evaluate_quote_freshness(
        data_mode="delayed",
        quote_time=now - timedelta(minutes=5),
        received_at=now,
        now=now,
    )
    manual = evaluate_quote_freshness(
        data_mode="manual",
        quote_time=None,
        received_at=now,
        now=now,
    )
    eod = evaluate_quote_freshness(
        data_mode="eod",
        quote_time=now - timedelta(hours=4),
        received_at=now,
        now=now,
    )

    assert delayed.freshness_status == "delayed"
    assert delayed.actionability_status == "analysis_only"
    assert manual.freshness_status == "manual"
    assert manual.actionability_status == "analysis_only"
    assert eod.freshness_status == "eod_only"
    assert eod.actionability_status == "analysis_only"


def test_synthetic_and_unavailable_quotes_are_never_actionable() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)

    synthetic = evaluate_quote_freshness(
        data_mode="synthetic",
        quote_time=now,
        received_at=now,
        now=now,
        freshness_scope="underlying_quote",
    )
    unavailable = evaluate_quote_freshness(
        data_mode="unavailable",
        quote_time=None,
        received_at=now,
        now=now,
        freshness_scope="option_quote",
    )

    assert synthetic.freshness_scope == "underlying_quote"
    assert synthetic.freshness_status == "fresh"
    assert synthetic.actionability_status == "analysis_only"
    assert unavailable.freshness_scope == "option_quote"
    assert unavailable.freshness_status == "unavailable"
    assert unavailable.actionability_status == "blocked_unknown_quote"
    assert unavailable.reason == "market quote is unavailable"


def test_cached_and_indicative_quotes_are_analysis_only_even_when_recent() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)

    cached = evaluate_quote_freshness(
        data_mode="cached",
        quote_time=now - timedelta(seconds=30),
        received_at=now,
        now=now,
    )
    indicative = evaluate_quote_freshness(
        data_mode="indicative",
        quote_time=now - timedelta(seconds=30),
        received_at=now,
        now=now,
    )

    assert cached.freshness_status == "fresh"
    assert cached.actionability_status == "analysis_only"
    assert indicative.freshness_status == "fresh"
    assert indicative.actionability_status == "analysis_only"


def test_stale_or_unknown_quote_is_blocked_not_actionable() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)

    stale = evaluate_quote_freshness(
        data_mode="live",
        quote_time=now - timedelta(seconds=DEFAULT_MAX_QUOTE_AGE_SECONDS + 1),
        received_at=now,
        now=now,
    )
    unknown = evaluate_quote_freshness(
        data_mode="unknown",
        quote_time=None,
        received_at=None,
        now=now,
    )

    assert stale.freshness_status == "stale"
    assert stale.actionability_status == "blocked_stale_quote"
    assert unknown.freshness_status == "unknown"
    assert unknown.actionability_status == "blocked_unknown_quote"


def test_provider_error_blocks_quote_actionability() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)

    decision = evaluate_quote_freshness(
        data_mode="live",
        quote_time=now,
        received_at=now,
        now=now,
        provider_error=True,
    )

    assert decision.freshness_status == "error"
    assert decision.actionability_status == "blocked_provider_error"


def test_manual_review_requirement_overrides_other_non_error_statuses() -> None:
    actionability = classify_quote_actionability(
        data_mode="live",
        freshness_status="fresh",
        manual_review_required=True,
    )

    assert actionability == "manual_review_required"


def test_freshness_policy_rejects_invalid_values() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="data_mode"):
        classify_quote_freshness(
            data_mode="broker_sync",
            quote_time=now,
            received_at=now,
            now=now,
        )

    with pytest.raises(ValueError, match="freshness_status"):
        classify_quote_actionability(data_mode="live", freshness_status="cached")
