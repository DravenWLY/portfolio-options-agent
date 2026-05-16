from sqlalchemy import select
from sqlalchemy.orm import Session

import pytest

from app.models.account import Account
from app.models.report_thread import ReportThread
from app.models.user import User


pytestmark = pytest.mark.db


def test_report_thread_can_be_created_and_queried(db_session: Session) -> None:
    user = User(display_name="Demo Report User", email="report-user@example.com")
    db_session.add(user)
    db_session.flush()

    account = Account(
        user_id=user.id,
        broker_name="Demo Broker",
        account_type="taxable_individual",
        display_name="Demo Taxable Account",
    )
    db_session.add(account)
    db_session.flush()

    report_thread = ReportThread(
        user_id=user.id,
        account_id=account.id,
        title="Synthetic portfolio review",
        report_type="portfolio_review",
        status="draft",
    )
    db_session.add(report_thread)
    db_session.commit()

    saved = db_session.scalar(select(ReportThread).where(ReportThread.id == report_thread.id))

    assert saved is not None
    assert saved.user_id == user.id
    assert saved.account_id == account.id
    assert saved.title == "Synthetic portfolio review"
    assert saved.report_type == "portfolio_review"
    assert saved.status == "draft"
    assert saved.deleted_at is None


def test_report_thread_defaults(db_session: Session) -> None:
    user = User(display_name="Demo Defaults User", email="report-defaults@example.com")
    db_session.add(user)
    db_session.flush()

    report_thread = ReportThread(user_id=user.id, title="Synthetic default report")
    db_session.add(report_thread)
    db_session.commit()
    db_session.refresh(report_thread)

    assert report_thread.account_id is None
    assert report_thread.report_type == "portfolio_report"
    assert report_thread.status == "draft"
    assert report_thread.created_at is not None
    assert report_thread.updated_at is not None
    assert report_thread.deleted_at is None
