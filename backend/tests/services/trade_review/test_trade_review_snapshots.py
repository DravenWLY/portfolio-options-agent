from datetime import UTC, datetime

import pytest

from app.services.market_data.snapshots import MarketDataSnapshotReference
from app.services.trade_review import MarketSnapshotResolver


pytestmark = [pytest.mark.unit]


def _reference(actionability_status: str) -> MarketDataSnapshotReference:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)
    return MarketDataSnapshotReference(
        snapshot_id="snapshot-1",
        kind="stock_quote",
        purpose="report_input_snapshot",
        provider="manual",
        stable_key="VOO",
        captured_at=now,
        quote_time=now,
        freshness_scope="market_quote",
        data_mode="manual",
        freshness_status="manual",
        actionability_status=actionability_status,
    )


def test_market_snapshot_resolver_preserves_market_freshness_and_actionability() -> None:
    snapshot = MarketSnapshotResolver().resolve(quote_references=(_reference("analysis_only"),))

    assert snapshot.quote_references[0].freshness_scope == "market_quote"
    assert snapshot.quote_references[0].actionability_status == "analysis_only"
    assert snapshot.manual_review_required is True


def test_market_snapshot_resolver_flags_missing_symbols() -> None:
    snapshot = MarketSnapshotResolver().resolve(
        quote_references=(_reference("actionable_snapshot"),),
        missing_symbols=(" hood ", ""),
    )

    assert snapshot.missing_symbols == ("HOOD",)
    assert snapshot.manual_review_required is True
