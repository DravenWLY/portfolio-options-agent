"""Role vocabulary and prompt-boundary metadata for Phase 19A."""

from dataclasses import dataclass

from app.services.agent_team.llm_provider import AGENT_TEAM_ROLES, AgentTeamRole


PUBLIC_ANALYST_ROLES: tuple[AgentTeamRole, ...] = (
    "fundamentals_analyst",
    "news_analyst",
    "technical_analyst",
)
PORTFOLIO_AWARE_ROLES: tuple[AgentTeamRole, ...] = (
    "risk_management_agent",
    "portfolio_manager_agent",
)


@dataclass(frozen=True)
class AgentTeamRoleDefinition:
    role_name: AgentTeamRole
    display_name: str
    data_boundary: str
    may_receive_portfolio_evidence: bool


_ROLE_DEFINITIONS = {
    "fundamentals_analyst": AgentTeamRoleDefinition(
        role_name="fundamentals_analyst",
        display_name="Fundamentals Analyst",
        data_boundary="public_ticker_company_evidence_only",
        may_receive_portfolio_evidence=False,
    ),
    "news_analyst": AgentTeamRoleDefinition(
        role_name="news_analyst",
        display_name="News Analyst",
        data_boundary="public_news_and_mock_macro_evidence_only",
        may_receive_portfolio_evidence=False,
    ),
    "technical_analyst": AgentTeamRoleDefinition(
        role_name="technical_analyst",
        display_name="Technical Analyst",
        data_boundary="public_or_mock_market_context_only",
        may_receive_portfolio_evidence=False,
    ),
    "risk_management_agent": AgentTeamRoleDefinition(
        role_name="risk_management_agent",
        display_name="Risk Manager",
        data_boundary="sanitized_deterministic_review_evidence",
        may_receive_portfolio_evidence=True,
    ),
    "portfolio_manager_agent": AgentTeamRoleDefinition(
        role_name="portfolio_manager_agent",
        display_name="Portfolio Manager",
        data_boundary="prior_role_summaries_and_sanitized_deterministic_evidence",
        may_receive_portfolio_evidence=True,
    ),
}


def role_definition(role_name: AgentTeamRole) -> AgentTeamRoleDefinition:
    return _ROLE_DEFINITIONS[role_name]


def role_registry() -> tuple[AgentTeamRoleDefinition, ...]:
    return tuple(_ROLE_DEFINITIONS[role] for role in AGENT_TEAM_ROLES)
