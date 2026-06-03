"""Safe API/read schemas for the Phase 19A agent-team analysis console."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.actionability import ReviewActionabilityStatus
from app.schemas.trade_review_workspace import TradeReviewPortfolioPreviewRequest
from app.services.agent_team.llm_provider import (
    AGENT_TEAM_ROLES,
    LLM_PROVIDER_STATUSES,
    AgentTeamRole,
    LLMProviderStatus,
    find_prohibited_llm_phrases,
)
from app.services.agent_team.output_safety import validate_llm_provider_output
from app.services.privacy import FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS, find_forbidden_keys


AgentTeamRunStatus = Literal["completed", "partially_completed", "failed"]


class AgentTeamAnalysisPreviewRequest(TradeReviewPortfolioPreviewRequest):
    """Request for a stateless mock agent-team analysis preview."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AgentTeamRoleOutputRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    role_name: AgentTeamRole
    display_name: str
    status: Literal["completed", "unavailable", "skipped"]
    provider_status: LLMProviderStatus
    content_markdown: str | None
    is_mock: bool
    unavailable_reason: str | None = None


class AgentTeamStageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    stage: str
    status: str
    role_name: AgentTeamRole | None = None
    display_name: str | None = None
    provider_status: LLMProviderStatus | None = None
    unavailable_reason: str | None = None


class AgentTeamProviderWarningRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    code: str
    message: str


class AgentTeamAnalysisConsoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    run_reference: str
    workflow_version: str
    run_status: AgentTeamRunStatus
    generated_at: datetime
    review_flow_label: str
    review_actionability_status: ReviewActionabilityStatus
    broker_snapshot_freshness: dict[str, object]
    market_quote_freshness: dict[str, object]
    deterministic_evidence_summary: dict[str, object]
    role_outputs: tuple[AgentTeamRoleOutputRead, ...]
    final_synthesis: str | None
    provider_warnings: tuple[AgentTeamProviderWarningRead, ...]
    stages: tuple[AgentTeamStageRead, ...]
    safety_flags: tuple[str, ...]

    @model_validator(mode="after")
    def analysis_console_payload_must_be_safe(self) -> "AgentTeamAnalysisConsoleRead":
        validate_agent_team_console_payload(self.model_dump(mode="python"))
        return self


def validate_agent_team_console_payload(payload: object) -> None:
    forbidden = find_forbidden_keys(payload, forbidden_keys=FORBIDDEN_TRADE_REVIEW_WORKSPACE_KEYS)
    if forbidden:
        blocked = ", ".join(sorted(forbidden))
        raise ValueError(f"agent-team console payload contains forbidden private fields: {blocked}")
    # Reuse provider phrase validation for user-visible text while allowing safe strategy labels in structural fields.
    prohibited = find_prohibited_llm_phrases(payload)
    if prohibited:
        blocked = ", ".join(sorted(prohibited))
        raise ValueError(f"agent-team console payload contains prohibited phrase(s): {blocked}")
    validate_llm_provider_output(_provider_validated_subset(payload), label="agent-team console text")


def _provider_validated_subset(payload: object) -> object:
    """Return generated text fields for hardened provider-output validation."""

    if not isinstance(payload, dict):
        return payload
    return {
        "role_outputs": [
            {
                "role_name": output.get("role_name"),
                "content_markdown": output.get("content_markdown"),
                "unavailable_reason": output.get("unavailable_reason"),
            }
            for output in payload.get("role_outputs", ())
        ],
        "final_synthesis": payload.get("final_synthesis"),
        "provider_warnings": payload.get("provider_warnings", ()),
        "safety_flags": payload.get("safety_flags", ()),
    }


def supported_agent_team_roles() -> tuple[str, ...]:
    return AGENT_TEAM_ROLES


def supported_provider_statuses() -> tuple[str, ...]:
    return LLM_PROVIDER_STATUSES
