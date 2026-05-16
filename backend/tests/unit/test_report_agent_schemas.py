from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.agent_runs import AgentRunCreate, AgentStepCreate
from app.schemas.reports import ReportMessageCreate, ReportThreadCreate


pytestmark = pytest.mark.unit


def test_report_thread_create_schema() -> None:
    account_id = uuid4()
    payload = ReportThreadCreate(
        account_id=account_id,
        title="Synthetic report",
        report_type="portfolio_review",
        status="draft",
    )

    assert payload.account_id == account_id
    assert payload.title == "Synthetic report"
    assert payload.report_type == "portfolio_review"
    assert payload.status == "draft"


def test_report_message_create_schema_supports_markdown_and_json() -> None:
    payload = ReportMessageCreate(
        sender_type="system",
        message_type="markdown_report",
        content_markdown="# Synthetic",
        content_json={"source": "deterministic_template"},
        sequence=1,
    )

    assert payload.visibility == "private"
    assert payload.content_json == {"source": "deterministic_template"}


def test_agent_run_create_schema_exposes_traceability_fields() -> None:
    payload = AgentRunCreate(
        input_snapshot_json={"input": "synthetic"},
        output_snapshot_json={"output": "synthetic"},
        calculation_version="calc-v1",
        data_freshness_snapshot={"broker_portfolio": "fresh"},
    )

    assert payload.run_type == "portfolio_analysis"
    assert payload.status == "queued"
    assert payload.input_snapshot_json == {"input": "synthetic"}
    assert payload.output_snapshot_json == {"output": "synthetic"}
    assert payload.calculation_version == "calc-v1"
    assert payload.data_freshness_snapshot == {"broker_portfolio": "fresh"}


def test_agent_run_create_rejects_invalid_time_order() -> None:
    started_at = datetime.now(UTC)

    with pytest.raises(ValidationError):
        AgentRunCreate(started_at=started_at, completed_at=started_at - timedelta(seconds=1))


def test_agent_step_create_schema_exposes_traceability_and_cost_fields() -> None:
    payload = AgentStepCreate(
        agent_run_id=uuid4(),
        step_order=1,
        step_key="load_context",
        step_type="deterministic_context",
        input_snapshot_json={"input": "synthetic"},
        output_snapshot_json={"output": "synthetic"},
        calculation_version="step-v1",
        data_freshness_snapshot={"broker_portfolio": "fresh"},
        tokens_in=0,
        tokens_out=0,
        estimated_cost="0",
    )

    assert payload.status == "queued"
    assert payload.input_snapshot_json == {"input": "synthetic"}
    assert payload.output_snapshot_json == {"output": "synthetic"}
    assert payload.calculation_version == "step-v1"
    assert payload.tokens_in == 0
    assert payload.tokens_out == 0
    assert payload.estimated_cost == 0


def test_report_and_agent_schemas_do_not_expose_secret_fields() -> None:
    schema_names = [
        ReportThreadCreate,
        ReportMessageCreate,
        AgentRunCreate,
        AgentStepCreate,
    ]

    for schema in schema_names:
        fields = set(schema.model_fields)
        assert "secret_ref" not in fields
        assert "encrypted_secret_ref" not in fields
        assert "api_key" not in fields
        assert "access_token" not in fields
