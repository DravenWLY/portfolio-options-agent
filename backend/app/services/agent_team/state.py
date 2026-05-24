"""Typed state and stage contracts for the Phase 19A mock agent team."""

from dataclasses import asdict, dataclass, field
from datetime import datetime

from app.schemas.actionability import ReviewActionabilityStatus
from app.services.agent_team.llm_provider import AgentTeamRole, LLMProviderResponse
from app.services.agent_team.output_safety import validate_llm_provider_output
from app.services.agent_team.prompt_safety import validate_agent_team_text


AGENT_TEAM_WORKFLOW_VERSION = "agent-team-analysis-v1"
DEFAULT_AGENT_TEAM_STAGE_ORDER = (
    "validate_trade_intent",
    "build_deterministic_evidence_bundle",
    "classify_actionability",
    "prepare_public_evidence_context",
    "fundamentals_analyst",
    "news_analyst",
    "technical_analyst",
    "risk_management_agent",
    "portfolio_manager_agent",
    "compose_analysis_console_output",
    "persist_run_steps",
)


@dataclass(frozen=True)
class AgentTeamStageStatus:
    stage: str
    status: str
    role_name: AgentTeamRole | None = None
    provider_status: str | None = None
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        validate_agent_team_text(asdict(self), label="agent-team stage status")


@dataclass(frozen=True)
class AgentTeamRoleOutput:
    role_name: AgentTeamRole
    status: str
    content_markdown: str | None
    provider_status: str
    is_mock: bool
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        validate_llm_provider_output(asdict(self), label="agent-team role output")

    @classmethod
    def from_provider_response(cls, response: LLMProviderResponse) -> "AgentTeamRoleOutput":
        return cls(
            role_name=response.role_name,
            status="completed" if response.status == "ok" else "unavailable",
            content_markdown=response.content_markdown,
            provider_status=response.status,
            is_mock=response.is_mock,
            unavailable_reason=response.error_message,
        )


@dataclass(frozen=True)
class AgentTeamAnalysisState:
    run_reference: str
    workflow_version: str
    generated_at: datetime
    review_flow_label: str
    review_actionability_status: ReviewActionabilityStatus
    broker_snapshot_freshness: dict[str, object]
    market_quote_freshness: dict[str, object]
    deterministic_evidence_summary: dict[str, object]
    role_outputs: tuple[AgentTeamRoleOutput, ...] = ()
    stage_statuses: tuple[AgentTeamStageStatus, ...] = ()
    provider_warnings: tuple[str, ...] = ()
    final_synthesis: str | None = None
    run_status: str = "completed"
    safety_flags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        validate_llm_provider_output(asdict(self), label="agent-team analysis state")
