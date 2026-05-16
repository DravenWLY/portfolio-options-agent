from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

import pytest

from app.models.agent_run import AgentRun
from app.models.agent_step import AgentStep
from app.models.user import User


pytestmark = pytest.mark.db


def _create_agent_run(db_session: Session) -> AgentRun:
    user = User(display_name="Demo Step User", email="agent-step-user@example.com")
    db_session.add(user)
    db_session.flush()

    run = AgentRun(user_id=user.id, status="running")
    db_session.add(run)
    db_session.flush()
    return run


def test_agent_steps_are_ordered_within_run(db_session: Session) -> None:
    run = _create_agent_run(db_session)

    second_step = AgentStep(
        agent_run_id=run.id,
        step_order=2,
        step_key="compose_report",
        step_type="deterministic_report",
        status="completed",
        input_snapshot_json={"summary": "synthetic"},
        output_snapshot_json={"markdown": "# Synthetic"},
        calculation_version="report-v1",
        data_freshness_snapshot={"broker_portfolio": "fresh"},
        tokens_in=0,
        tokens_out=0,
        estimated_cost=Decimal("0.0000"),
    )
    first_step = AgentStep(
        agent_run_id=run.id,
        step_order=1,
        step_key="load_context",
        step_type="deterministic_context",
        status="completed",
        input_snapshot_json={"account_id": "synthetic"},
        output_snapshot_json={"positions": []},
        calculation_version="context-v1",
        data_freshness_snapshot={"broker_portfolio": "fresh"},
    )
    db_session.add_all([second_step, first_step])
    db_session.commit()

    steps = list(
        db_session.scalars(
            select(AgentStep).where(AgentStep.agent_run_id == run.id).order_by(AgentStep.step_order)
        )
    )

    assert [step.step_order for step in steps] == [1, 2]
    assert steps[0].step_key == "load_context"
    assert steps[0].input_snapshot_json == {"account_id": "synthetic"}
    assert steps[0].output_snapshot_json == {"positions": []}
    assert steps[0].calculation_version == "context-v1"
    assert steps[1].step_key == "compose_report"
    assert steps[1].tokens_in == 0
    assert steps[1].tokens_out == 0
    assert steps[1].estimated_cost == Decimal("0.0000")


def test_agent_step_defaults(db_session: Session) -> None:
    run = _create_agent_run(db_session)

    step = AgentStep(
        agent_run_id=run.id,
        step_order=1,
        step_key="queued_step",
        step_type="deterministic_context",
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)

    assert step.status == "queued"
    assert step.started_at is None
    assert step.completed_at is None
    assert step.input_snapshot_json is None
    assert step.output_snapshot_json is None
    assert step.error is None
    assert step.created_at is not None
    assert step.updated_at is not None
