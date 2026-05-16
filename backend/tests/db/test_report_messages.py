from sqlalchemy import select
from sqlalchemy.orm import Session

import pytest

from app.models.report_message import ReportMessage
from app.models.report_thread import ReportThread
from app.models.user import User


pytestmark = pytest.mark.db


def _create_report_thread(db_session: Session) -> ReportThread:
    user = User(display_name="Demo Message User", email="report-message-user@example.com")
    db_session.add(user)
    db_session.flush()

    report_thread = ReportThread(user_id=user.id, title="Synthetic report thread")
    db_session.add(report_thread)
    db_session.flush()
    return report_thread


def test_report_messages_belong_to_thread_and_query_in_sequence_order(db_session: Session) -> None:
    report_thread = _create_report_thread(db_session)

    second_message = ReportMessage(
        thread_id=report_thread.id,
        sender_type="agent",
        message_type="markdown_report",
        content_markdown="## Synthetic final report",
        content_json={"section": "final"},
        sequence=2,
    )
    first_message = ReportMessage(
        thread_id=report_thread.id,
        sender_type="user",
        message_type="user_input",
        content_markdown="Review this synthetic account.",
        content_json={"request": "portfolio_review"},
        sequence=1,
    )
    db_session.add_all([second_message, first_message])
    db_session.commit()

    messages = list(
        db_session.scalars(
            select(ReportMessage)
            .where(ReportMessage.thread_id == report_thread.id)
            .order_by(ReportMessage.sequence)
        )
    )

    assert [message.sequence for message in messages] == [1, 2]
    assert messages[0].message_type == "user_input"
    assert messages[0].sender_type == "user"
    assert messages[0].content_json == {"request": "portfolio_review"}
    assert messages[1].message_type == "markdown_report"
    assert messages[1].content_markdown == "## Synthetic final report"
    assert messages[1].content_json == {"section": "final"}


def test_report_message_defaults(db_session: Session) -> None:
    report_thread = _create_report_thread(db_session)

    message = ReportMessage(
        thread_id=report_thread.id,
        sender_type="system",
        message_type="system_event",
        content_markdown="Synthetic report created.",
        sequence=1,
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)

    assert message.visibility == "private"
    assert message.content_json is None
    assert message.created_at is not None
    assert message.updated_at is not None
    assert message.deleted_at is None
