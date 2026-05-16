from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

AgentRunStatus = Literal["queued", "running", "waiting_retry", "failed", "cancelled", "completed", "partially_completed"]
AgentStepStatus = Literal["queued", "running", "failed", "cancelled", "completed", "skipped"]


class AgentRunCreate(BaseModel):
    account_id: UUID | None = None
    report_thread_id: UUID | None = None
    run_type: str = Field(default="portfolio_analysis", min_length=1, max_length=80)
    status: AgentRunStatus = "queued"
    provider: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    token_budget: int | None = Field(default=None, ge=0)
    cost_budget: Decimal | None = Field(default=None, ge=0)
    input_snapshot_json: dict[str, Any] | None = None
    output_snapshot_json: dict[str, Any] | None = None
    calculation_version: str | None = Field(default=None, max_length=80)
    data_freshness_snapshot: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_completion_order(self) -> "AgentRunCreate":
        if self.started_at is not None and self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must be after started_at")
        return self


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    account_id: UUID | None
    report_thread_id: UUID | None
    run_type: str
    status: str
    provider: str | None
    model: str | None
    token_budget: int | None
    cost_budget: Decimal | None
    input_snapshot_json: dict[str, Any] | None
    output_snapshot_json: dict[str, Any] | None
    calculation_version: str | None
    data_freshness_snapshot: dict[str, Any] | None
    started_at: datetime | None
    completed_at: datetime | None
    error: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class AgentStepCreate(BaseModel):
    agent_run_id: UUID
    step_order: int = Field(ge=1)
    step_key: str = Field(min_length=1, max_length=120)
    step_type: str = Field(min_length=1, max_length=80)
    status: AgentStepStatus = "queued"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    input_snapshot_json: dict[str, Any] | None = None
    output_snapshot_json: dict[str, Any] | None = None
    calculation_version: str | None = Field(default=None, max_length=80)
    data_freshness_snapshot: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    tokens_in: int | None = Field(default=None, ge=0)
    tokens_out: int | None = Field(default=None, ge=0)
    estimated_cost: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_completion_order(self) -> "AgentStepCreate":
        if self.started_at is not None and self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must be after started_at")
        return self


class AgentStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_run_id: UUID
    step_order: int
    step_key: str
    step_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    input_snapshot_json: dict[str, Any] | None
    output_snapshot_json: dict[str, Any] | None
    calculation_version: str | None
    data_freshness_snapshot: dict[str, Any] | None
    error: dict[str, Any] | None
    tokens_in: int | None
    tokens_out: int | None
    estimated_cost: Decimal | None
    created_at: datetime
    updated_at: datetime
