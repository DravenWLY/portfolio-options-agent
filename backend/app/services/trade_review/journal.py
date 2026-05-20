from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TradeReviewReportLink:
    """Audit link from a deterministic trade review to report history."""

    trade_intent_id: str
    report_thread_id: str
    created_at: datetime
    report_message_id: str | None = None
    journal_entry_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.trade_intent_id, "trade_intent_id")
        _require_text(self.report_thread_id, "report_thread_id")
        if self.report_message_id is not None:
            _require_text(self.report_message_id, "report_message_id")
        if self.journal_entry_id is not None:
            _require_text(self.journal_entry_id, "journal_entry_id")


@dataclass(frozen=True)
class JournalServiceBoundary:
    """Future journal boundary.

    Phase 14 only defines read-only audit links. Full journal notes, activity
    sync, realized P&L, and lifecycle reconstruction are later phases.
    """

    supports_user_notes: bool = False
    supports_post_review_tracking: bool = False
    supports_broker_activity_sync: bool = False
    supports_order_tracking: bool = False


def link_trade_review_to_report(
    *,
    trade_intent_id: str,
    report_thread_id: str,
    created_at: datetime,
    report_message_id: str | None = None,
    journal_entry_id: str | None = None,
) -> TradeReviewReportLink:
    return TradeReviewReportLink(
        trade_intent_id=trade_intent_id,
        report_thread_id=report_thread_id,
        created_at=created_at,
        report_message_id=report_message_id,
        journal_entry_id=journal_entry_id,
    )


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
