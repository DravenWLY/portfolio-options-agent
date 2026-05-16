import pytest
from sqlalchemy.orm import Session

from app.models.report_thread import ReportThread
from app.models.user import User
from app.services.reports.markdown import persist_basic_markdown_report, render_basic_markdown_report


pytestmark = [pytest.mark.unit, pytest.mark.db]


def test_render_basic_markdown_report_is_deterministic_and_safety_scoped() -> None:
    markdown = render_basic_markdown_report(
        title="Synthetic Portfolio Review",
        portfolio_summary={
            "total_cash": "1000.00",
            "stock_market_value": "2500.00",
            "option_market_value": "-50.00",
            "total_internal_value": "3450.00",
            "data_freshness_statuses": ["fresh"],
            "broker_data_warnings": [],
        },
        broker_freshness={"data_freshness_status": "fresh"},
    )

    assert markdown.startswith("# Synthetic Portfolio Review")
    assert "This deterministic report was generated from structured backend data." in markdown
    assert "It does not include LLM output, TradingAgents research, market data API calls, or trade execution." in markdown
    assert "- Total cash: 1000.00" in markdown
    assert "- Broker freshness status: fresh" in markdown
    assert "Manual decision support only" in markdown


def test_persist_basic_markdown_report_creates_report_message(db_session: Session) -> None:
    user = User(display_name="Demo Markdown User", email="markdown-user@example.com")
    db_session.add(user)
    db_session.flush()
    thread = ReportThread(user_id=user.id, title="Synthetic markdown thread")
    db_session.add(thread)
    db_session.commit()

    message = persist_basic_markdown_report(
        db_session,
        thread_id=thread.id,
        title="Synthetic Portfolio Review",
        portfolio_summary={
            "total_cash": "1000.00",
            "stock_market_value": "2500.00",
            "option_market_value": "-50.00",
            "total_internal_value": "3450.00",
            "data_freshness_statuses": ["fresh"],
            "broker_data_warnings": [],
        },
        broker_freshness={"data_freshness_status": "fresh"},
    )

    assert message.thread_id == thread.id
    assert message.sender_type == "system"
    assert message.message_type == "markdown_report"
    assert message.sequence == 1
    assert message.content_markdown is not None
    assert "Synthetic Portfolio Review" in message.content_markdown
    assert message.content_json == {
        "generator": "deterministic_template",
        "portfolio_summary": {
            "total_cash": "1000.00",
            "stock_market_value": "2500.00",
            "option_market_value": "-50.00",
            "total_internal_value": "3450.00",
            "data_freshness_statuses": ["fresh"],
            "broker_data_warnings": [],
        },
        "broker_freshness": {"data_freshness_status": "fresh"},
    }
