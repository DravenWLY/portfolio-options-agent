# DEPRECATED (P34A-T11C): legacy P19/P25 Agent Console preview path. Bug-fix
# only; superseded by the tool-mediated saved-report pipeline. Do not extend.
"""Role-specific safe prompt-input assembly for Phase 19C."""

from dataclasses import asdict, dataclass, field

from app.services.agent_team.legacy_console.evidence import PublicEvidenceBundle
from app.services.agent_team.legacy_console.evidence_projection import (
    AgentSafeDeterministicEvidenceProjection,
    projection_snapshot,
)
from app.services.agent_team.llm_clients.contracts import AgentTeamRole
from app.services.agent_team.safety.prompt_safety import validate_agent_team_text
from app.services.agent_team.agents.roles import PUBLIC_ANALYST_ROLES, role_definition


@dataclass(frozen=True)
class AgentTeamPromptInput:
    """Stable structured prompt input for one agent role."""

    role_name: AgentTeamRole
    data_boundary: str
    output_mode: str
    public_context: dict[str, object]
    deterministic_metric_source: str
    portfolio_evidence_allowed: bool
    deterministic_evidence: dict[str, object] | None = None
    prior_role_summary_count: int = 0
    prior_role_summaries: tuple[str, ...] = ()
    safety_instructions: tuple[str, ...] = field(
        default_factory=lambda: (
            "Use only supplied structured evidence.",
            "Deterministic backend services own all financial calculations.",
            "Provide analysis-only educational commentary.",
            "Do not create new numeric financial metrics or execution instructions.",
        )
    )

    def __post_init__(self) -> None:
        validate_agent_team_text(asdict(self), label=f"{self.role_name} prompt input")

    def snapshot(self) -> dict[str, object]:
        return asdict(self)


def build_agent_team_prompt_input(
    *,
    role_name: AgentTeamRole,
    public_evidence: PublicEvidenceBundle,
    deterministic_evidence: AgentSafeDeterministicEvidenceProjection | None = None,
    prior_role_summaries: tuple[str, ...] = (),
) -> AgentTeamPromptInput:
    """Build one role-specific prompt input without private portfolio data."""

    definition = role_definition(role_name)
    public_context = {
        "ticker": public_evidence.ticker,
        "company_name": public_evidence.company_name,
        "evidence_mode": public_evidence.evidence_mode,
        "fundamentals_status": _availability(public_evidence.fundamentals_context),
        "news_status": _availability(public_evidence.news_context),
        "macro_status": _availability(public_evidence.macro_context),
        "technical_status": _availability(public_evidence.technical_context),
    }
    if role_name in PUBLIC_ANALYST_ROLES:
        return AgentTeamPromptInput(
            role_name=role_name,
            data_boundary=definition.data_boundary,
            output_mode="analysis_only_public_evidence",
            public_context=public_context,
            deterministic_metric_source="backend_owned_not_llm_generated",
            portfolio_evidence_allowed=False,
        )
    if deterministic_evidence is None:
        raise ValueError(f"{role_name} requires agent-safe deterministic evidence")
    return AgentTeamPromptInput(
        role_name=role_name,
        data_boundary=definition.data_boundary,
        output_mode="analysis_only_portfolio_aware_evidence",
        public_context=public_context,
        deterministic_metric_source="backend_owned_not_llm_generated",
        portfolio_evidence_allowed=True,
        deterministic_evidence=projection_snapshot(deterministic_evidence),
        prior_role_summary_count=len(prior_role_summaries),
        prior_role_summaries=_prompt_safe_prior_summaries(prior_role_summaries),
    )


def build_all_role_prompt_inputs(
    *,
    role_names: tuple[AgentTeamRole, ...],
    public_evidence: PublicEvidenceBundle,
    deterministic_evidence: AgentSafeDeterministicEvidenceProjection,
    prior_role_summaries: tuple[str, ...] = (),
) -> tuple[AgentTeamPromptInput, ...]:
    return tuple(
        build_agent_team_prompt_input(
            role_name=role_name,
            public_evidence=public_evidence,
            deterministic_evidence=deterministic_evidence if role_name not in PUBLIC_ANALYST_ROLES else None,
            prior_role_summaries=prior_role_summaries,
        )
        for role_name in role_names
    )


def _availability(text: str) -> str:
    lowered = text.lower()
    if "unavailable" in lowered:
        return "unavailable"
    if "synthetic" in lowered or "mock" in lowered:
        return "synthetic"
    return "available"


def _prompt_safe_prior_summaries(summaries: tuple[str, ...]) -> tuple[str, ...]:
    safe: list[str] = []
    for summary in summaries:
        try:
            validate_agent_team_text(summary, label="prior role summary prompt input")
        except ValueError:
            safe.append("Prior role output passed output safety but was withheld from strict prompt input.")
        else:
            safe.append(summary)
    return tuple(safe)
