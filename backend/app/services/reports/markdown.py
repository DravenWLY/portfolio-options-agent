from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.report_message import ReportMessage
from app.schemas.reports import ReportMessageCreate
from app.services.reports import crud


def render_basic_markdown_report(
    *,
    title: str,
    portfolio_summary: dict[str, Any],
    broker_freshness: dict[str, Any] | None = None,
) -> str:
    freshness_status = portfolio_summary.get("data_freshness_statuses") or []
    warnings = portfolio_summary.get("broker_data_warnings") or []
    broker_status = broker_freshness.get("data_freshness_status") if broker_freshness else "not_available"

    return "\n".join(
        [
            f"# {title}",
            "",
            "This deterministic report was generated from structured backend data.",
            "It does not include LLM output, TradingAgents research, market data API calls, or trade execution.",
            "",
            "## Portfolio Snapshot",
            f"- Total cash: {portfolio_summary.get('total_cash', '0')}",
            f"- Stock market value: {portfolio_summary.get('stock_market_value', '0')}",
            f"- Option market value: {portfolio_summary.get('option_market_value', '0')}",
            f"- Total internal value: {portfolio_summary.get('total_internal_value', '0')}",
            "",
            "## Data Freshness",
            f"- Portfolio freshness statuses: {', '.join(freshness_status) if freshness_status else 'not_available'}",
            f"- Broker freshness status: {broker_status}",
            f"- Broker warning count: {len(warnings)}",
            "",
            "## Safety Boundary",
            "- Manual decision support only.",
            "- Refresh broker and quote data before making any manual trading decision.",
        ]
    )


def persist_basic_markdown_report(
    db: Session,
    *,
    thread_id: UUID,
    title: str,
    portfolio_summary: dict[str, Any],
    broker_freshness: dict[str, Any] | None = None,
) -> ReportMessage:
    markdown = render_basic_markdown_report(
        title=title,
        portfolio_summary=portfolio_summary,
        broker_freshness=broker_freshness,
    )
    sequence = crud.next_message_sequence(db, thread_id)
    return crud.create_report_message(
        db,
        thread_id,
        ReportMessageCreate(
            sender_type="system",
            message_type="markdown_report",
            content_markdown=markdown,
            content_json={
                "generator": "deterministic_template",
                "portfolio_summary": portfolio_summary,
                "broker_freshness": broker_freshness,
            },
            sequence=sequence,
        ),
    )
