# DEPRECATED (P34A-T11C): legacy P19/P25 Agent Console preview path. Bug-fix
# only; superseded by the tool-mediated saved-report pipeline. Do not extend.
"""Prompt rendering for the Phase 19A mock agent team."""

from dataclasses import asdict

from app.services.agent_team.legacy_console.evidence import DeterministicEvidenceBundle, PublicEvidenceBundle
from app.services.agent_team.llm_clients.contracts import AgentTeamRole, LLMProviderMessage
from app.services.agent_team.legacy_console.prompt_inputs import AgentTeamPromptInput
from app.services.agent_team.safety.prompt_safety import validate_agent_team_text
from app.services.agent_team.agents.roles import PUBLIC_ANALYST_ROLES, role_definition


BASE_SYSTEM_RULES = (
    "You are a Portfolio Copilot analysis role. Use only the structured evidence provided. "
    "Deterministic backend services own all financial calculations. Provide analysis-only educational commentary. "
    "Do not invent metrics, give directive trading instructions, claim execution readiness, or promise outcomes."
)


def render_role_messages(
    *,
    role_name: AgentTeamRole,
    public_evidence: PublicEvidenceBundle,
    deterministic_evidence: DeterministicEvidenceBundle | None = None,
    prior_role_summaries: tuple[str, ...] = (),
) -> tuple[LLMProviderMessage, ...]:
    """Render safe provider messages for one Phase 19A role."""

    definition = role_definition(role_name)
    payload: dict[str, object] = {
        "role_name": role_name,
        "data_boundary": definition.data_boundary,
        "public_evidence": asdict(public_evidence),
    }
    if role_name in PUBLIC_ANALYST_ROLES:
        payload["portfolio_evidence_allowed"] = False
    else:
        if deterministic_evidence is None:
            raise ValueError(f"{role_name} requires deterministic evidence")
        payload["portfolio_evidence_allowed"] = True
        payload["deterministic_evidence"] = asdict(deterministic_evidence)
        payload["prior_role_summary_count"] = len(prior_role_summaries)
        payload["prior_role_summaries"] = prior_role_summaries
    validate_agent_team_text(payload, label=f"{role_name} prompt payload")
    system = LLMProviderMessage(role="system", content=BASE_SYSTEM_RULES)
    user = LLMProviderMessage(role="user", content=_render_prompt_text(payload))
    return (system, user)


def render_prompt_input_messages(prompt_input: AgentTeamPromptInput) -> tuple[LLMProviderMessage, ...]:
    """Render provider messages from the P19C role-specific prompt input."""

    payload = prompt_input.snapshot()
    validate_agent_team_text(payload, label=f"{prompt_input.role_name} prompt input payload")
    system = LLMProviderMessage(role="system", content=BASE_SYSTEM_RULES)
    user = LLMProviderMessage(role="user", content=_render_prompt_text(payload))
    return (system, user)


def _render_prompt_text(payload: dict[str, object]) -> str:
    lines = [
        f"Role: {payload['role_name']}",
        f"Data boundary: {payload['data_boundary']}",
        "Output mode: analysis-only educational commentary.",
        "Use provided structured evidence only; do not create new numeric financial metrics.",
        f"Payload: {payload}",
    ]
    text = "\n".join(lines)
    validate_agent_team_text(text, label="rendered role prompt")
    return text
