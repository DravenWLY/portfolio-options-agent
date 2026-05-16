from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

import pytest

from app.models.account import Account
from app.models.agent_run import AgentRun
from app.models.report_thread import ReportThread
from app.models.user import User


pytestmark = pytest.mark.db


def _create_user_account_and_thread(db_session: Session) -> tuple[User, Account, ReportThread]:
    user = User(display_name="Demo Agent User", email="agent-run-user@example.com")
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
        title="Synthetic agent report",
    )
    db_session.add(report_thread)
    db_session.flush()

    return user, account, report_thread


def test_agent_run_can_be_created_and_linked_to_report_thread(db_session: Session) -> None:
    user, account, report_thread = _create_user_account_and_thread(db_session)

    run = AgentRun(
        user_id=user.id,
        account_id=account.id,
        report_thread_id=report_thread.id,
        run_type="portfolio_context",
        status="completed",
        provider="deterministic",
        model="template",
        token_budget=0,
        cost_budget=Decimal("0.0000"),
        input_snapshot_json={"account_id": str(account.id), "positions": []},
        output_snapshot_json={"summary": "synthetic"},
        calculation_version="portfolio-context-v1",
        data_freshness_snapshot={"broker_portfolio": "fresh", "market_quote": "not_available"},
    )
    db_session.add(run)
    db_session.commit()

    saved = db_session.scalar(select(AgentRun).where(AgentRun.id == run.id))

    assert saved is not None
    assert saved.user_id == user.id
    assert saved.account_id == account.id
    assert saved.report_thread_id == report_thread.id
    assert saved.run_type == "portfolio_context"
    assert saved.status == "completed"
    assert saved.provider == "deterministic"
    assert saved.model == "template"
    assert saved.token_budget == 0
    assert saved.cost_budget == Decimal("0.0000")
    assert saved.input_snapshot_json == {"account_id": str(account.id), "positions": []}
    assert saved.output_snapshot_json == {"summary": "synthetic"}
    assert saved.calculation_version == "portfolio-context-v1"
    assert saved.data_freshness_snapshot == {"broker_portfolio": "fresh", "market_quote": "not_available"}
    assert saved.error is None


def test_agent_run_defaults(db_session: Session) -> None:
    user = User(display_name="Demo Agent Defaults", email="agent-run-defaults@example.com")
    db_session.add(user)
    db_session.flush()

    run = AgentRun(user_id=user.id)
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    assert run.account_id is None
    assert run.report_thread_id is None
    assert run.run_type == "portfolio_analysis"
    assert run.status == "queued"
    assert run.provider is None
    assert run.model is None
    assert run.input_snapshot_json is None
    assert run.output_snapshot_json is None
    assert run.calculation_version is None
    assert run.data_freshness_snapshot is None
    assert run.created_at is not None
    assert run.updated_at is not None
