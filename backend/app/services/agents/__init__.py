"""Deterministic custom-agent service boundaries."""

from app.services.agents.context_envelopes import (
    CONTEXT_ENVELOPE_TYPES,
    ContextEnvelope,
    make_actionability_context_envelope,
    make_context_envelope,
)
from app.services.agents.freshness_guardrail import (
    FreshnessGuardrail,
    FreshnessGuardrailAgent,
    FreshnessGuardrailAgentOutput,
)
from app.services.agents.orchestrator import (
    DEFAULT_AGENT_WORKFLOW_STAGES,
    AgentTeamOrchestrationContract,
    AgentTeamOrchestrationResult,
    AgentTeamStageOutput,
    OrchestratorStageContract,
    PortfolioAgentTeamOrchestrator,
    build_orchestration_contract,
)
from app.services.agents.portfolio_context import (
    HoldingsShapeSummary,
    PortfolioContextAgent,
    PortfolioContextAgentOutput,
    PortfolioFreshnessSummary,
    ReportHistoryReference,
)
from app.services.agents.report_composer import ReportComposerAgent, ReportComposerAgentOutput
from app.services.agents.roles import (
    ALL_AGENT_ROLES,
    MVP_AGENT_ROLES,
    OPTIONAL_FUTURE_AGENT_ROLES,
    P1_AGENT_ROLES,
    AgentRoleDefinition,
    role_registry,
)
from app.services.agents.trade_review import TradeReviewAgent, TradeReviewAgentOutput, TradeReviewExplanationSection

__all__ = [
    "ALL_AGENT_ROLES",
    "CONTEXT_ENVELOPE_TYPES",
    "DEFAULT_AGENT_WORKFLOW_STAGES",
    "FreshnessGuardrail",
    "FreshnessGuardrailAgent",
    "FreshnessGuardrailAgentOutput",
    "AgentRoleDefinition",
    "AgentTeamOrchestrationContract",
    "AgentTeamOrchestrationResult",
    "AgentTeamStageOutput",
    "ContextEnvelope",
    "HoldingsShapeSummary",
    "MVP_AGENT_ROLES",
    "OPTIONAL_FUTURE_AGENT_ROLES",
    "OrchestratorStageContract",
    "P1_AGENT_ROLES",
    "PortfolioAgentTeamOrchestrator",
    "PortfolioContextAgent",
    "PortfolioContextAgentOutput",
    "PortfolioFreshnessSummary",
    "ReportComposerAgent",
    "ReportComposerAgentOutput",
    "ReportHistoryReference",
    "TradeReviewAgent",
    "TradeReviewAgentOutput",
    "TradeReviewExplanationSection",
    "build_orchestration_contract",
    "make_actionability_context_envelope",
    "make_context_envelope",
    "role_registry",
]
