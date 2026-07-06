"""Agent Team role/agent layer (P34A-T11B onward).

Currently holds role vocabulary and prompt-boundary metadata (``roles``).
Deterministic role-finding builders and the live-prose overlay move here in
P34A-T11E. The old ``agent_team.roles`` path remains a compatibility shim.
"""

from app.services.agent_team.agents.roles import (
    PORTFOLIO_AWARE_ROLES,
    PUBLIC_ANALYST_ROLES,
    AgentTeamRoleDefinition,
    role_definition,
    role_registry,
)

__all__ = [
    "PORTFOLIO_AWARE_ROLES",
    "PUBLIC_ANALYST_ROLES",
    "AgentTeamRoleDefinition",
    "role_definition",
    "role_registry",
]
