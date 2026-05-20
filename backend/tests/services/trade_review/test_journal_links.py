from datetime import UTC, datetime

import pytest

from app.services.trade_review import JournalServiceBoundary, link_trade_review_to_report


pytestmark = [pytest.mark.unit]


def test_trade_review_report_link_traces_intent_to_report_history() -> None:
    now = datetime(2026, 5, 18, 15, 0, tzinfo=UTC)

    link = link_trade_review_to_report(
        trade_intent_id="review-1",
        report_thread_id="thread-1",
        report_message_id="message-1",
        created_at=now,
    )

    assert link.trade_intent_id == "review-1"
    assert link.report_thread_id == "thread-1"
    assert link.report_message_id == "message-1"
    assert link.journal_entry_id is None


def test_trade_review_report_link_rejects_empty_ids() -> None:
    with pytest.raises(ValueError, match="trade_intent_id"):
        link_trade_review_to_report(
            trade_intent_id=" ",
            report_thread_id="thread-1",
            created_at=datetime(2026, 5, 18, 15, 0, tzinfo=UTC),
        )


def test_journal_service_boundary_is_read_only_for_phase_14() -> None:
    boundary = JournalServiceBoundary()

    assert boundary.supports_user_notes is False
    assert boundary.supports_post_review_tracking is False
    assert boundary.supports_broker_activity_sync is False
    assert boundary.supports_order_tracking is False
