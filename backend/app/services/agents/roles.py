"""Shared agent role vocabulary and context-privacy policy."""

from dataclasses import dataclass
from typing import Literal, TypeAlias


AgentRoleName: TypeAlias = Literal[
    "portfolio_context_agent",
    "trade_review_agent",
    "risk_concentration_behavior",
    "freshness_guardrail_agent",
    "report_composer_agent",
    "market_data_agent",
    "news_research_evidence_agent",
    "bull_case_agent",
    "bear_case_agent",
    "tradingagents_public_research_adapter",
]

MVP_AGENT_ROLES: tuple[str, ...] = (
    "portfolio_context_agent",
    "trade_review_agent",
    "risk_concentration_behavior",
    "freshness_guardrail_agent",
    "report_composer_agent",
)
P1_AGENT_ROLES: tuple[str, ...] = (
    "market_data_agent",
    "news_research_evidence_agent",
    "bull_case_agent",
    "bear_case_agent",
)
OPTIONAL_FUTURE_AGENT_ROLES: tuple[str, ...] = ("tradingagents_public_research_adapter",)
PRIVATE_CONTEXT_AGENT_ROLES = frozenset(MVP_AGENT_ROLES)
ENVELOPE_ALLOWED_ROLE_NAMES = {
    "private_portfolio_safe_context": PRIVATE_CONTEXT_AGENT_ROLES,
    "deterministic_review_context": PRIVATE_CONTEXT_AGENT_ROLES,
    "actionability_context": PRIVATE_CONTEXT_AGENT_ROLES,
    "report_composition_context": PRIVATE_CONTEXT_AGENT_ROLES,
    "public_evidence_context": frozenset(
        {
            "market_data_agent",
            "news_research_evidence_agent",
            "bull_case_agent",
            "bear_case_agent",
            "tradingagents_public_research_adapter",
        }
    ),
    "llm_explanation_context": frozenset({"bull_case_agent", "bear_case_agent"}),
}
ALL_AGENT_ROLES: tuple[str, ...] = MVP_AGENT_ROLES + P1_AGENT_ROLES + OPTIONAL_FUTURE_AGENT_ROLES


@dataclass(frozen=True)
class AgentRoleDefinition:
    role_name: AgentRoleName
    role_group: str
    default_available: bool
    may_receive_private_context: bool


def role_registry() -> tuple[AgentRoleDefinition, ...]:
    """Return stable role vocabulary for Phase 16B and later."""

    return (
        AgentRoleDefinition("portfolio_context_agent", "mvp", True, True),
        AgentRoleDefinition("trade_review_agent", "mvp", True, True),
        AgentRoleDefinition("risk_concentration_behavior", "mvp", True, True),
        AgentRoleDefinition("freshness_guardrail_agent", "mvp", True, True),
        AgentRoleDefinition("report_composer_agent", "mvp", True, True),
        AgentRoleDefinition("market_data_agent", "p1", False, False),
        AgentRoleDefinition("news_research_evidence_agent", "p1", False, False),
        AgentRoleDefinition("bull_case_agent", "p1", False, False),
        AgentRoleDefinition("bear_case_agent", "p1", False, False),
        AgentRoleDefinition("tradingagents_public_research_adapter", "future_optional", False, False),
    )


def validate_role_envelope_compatibility(
    *,
    envelope_type: str,
    allowed_role_names: tuple[str, ...],
) -> None:
    """Reject role/envelope combinations that violate the private-data boundary."""

    unknown_roles = set(allowed_role_names) - set(ALL_AGENT_ROLES)
    if unknown_roles:
        blocked = ", ".join(sorted(unknown_roles))
        raise ValueError(f"context envelope contains unknown agent role(s): {blocked}")

    incompatible: set[str] = set()
    allowed_for_envelope = ENVELOPE_ALLOWED_ROLE_NAMES.get(envelope_type, frozenset())
    for role_name in allowed_role_names:
        if role_name not in allowed_for_envelope:
            incompatible.add(role_name)
    if incompatible:
        blocked = ", ".join(sorted(incompatible))
        raise ValueError(f"{envelope_type} is not compatible with agent role(s): {blocked}")
