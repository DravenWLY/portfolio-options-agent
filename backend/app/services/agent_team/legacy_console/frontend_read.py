# DEPRECATED (P34A-T11C): legacy P19/P25 Agent Console preview path. Bug-fix
# only; superseded by the tool-mediated saved-report pipeline. Do not extend.
"""Frontend/API read projection for the Phase 19A analysis console."""

from app.schemas.agent_team import (
    AgentTeamAnalysisConsoleRead,
    AgentTeamProviderWarningRead,
    AgentTeamRoleOutputRead,
    AgentTeamStageRead,
)
from app.services.agent_team.legacy_console.evidence_projection import unavailable_agent_scope_summary
from app.services.agent_team.llm_clients.contracts import AGENT_TEAM_ROLES
from app.services.agent_team.agents.roles import role_definition
from app.services.agent_team.legacy_console.run_state import AgentReviewRunState
from app.services.agent_team.legacy_console.state import AgentTeamAnalysisState


_REVIEW_RUN_STATUS_TO_CONSOLE = {
    "completed": "completed",
    "partially_completed": "partially_completed",
    "failed_safe": "failed",
}


def build_agent_team_analysis_console_read(state: AgentTeamAnalysisState) -> AgentTeamAnalysisConsoleRead:
    """Map internal agent-team state to the safe analysis-console contract.

    Display labels are backend-owned: ``display_name`` is populated verbatim from
    the role registry so the frontend renders it as-is (ADR 0009). Machine
    ``role_name`` values are preserved unchanged.
    """

    return AgentTeamAnalysisConsoleRead(
        run_reference=state.run_reference,
        workflow_version=state.workflow_version,
        run_status=state.run_status,
        generated_at=state.generated_at,
        review_flow_label=state.review_flow_label,
        review_actionability_status=state.review_actionability_status,
        broker_snapshot_freshness=state.broker_snapshot_freshness,
        market_quote_freshness=state.market_quote_freshness,
        deterministic_evidence_summary=state.deterministic_evidence_summary,
        scope_summary=unavailable_agent_scope_summary(),
        role_outputs=tuple(
            AgentTeamRoleOutputRead(
                role_name=output.role_name,
                display_name=role_definition(output.role_name).display_name,
                status=output.status,
                provider_status=output.provider_status,
                content_markdown=output.content_markdown,
                is_mock=output.is_mock,
                unavailable_reason=output.unavailable_reason,
            )
            for output in state.role_outputs
        ),
        final_synthesis=state.final_synthesis,
        provider_warnings=tuple(
            AgentTeamProviderWarningRead(
                code="mock_provider_role_unavailable",
                message=f"Mock provider returned {warning}. Deterministic evidence remains available.",
            )
            for warning in state.provider_warnings
        ),
        stages=tuple(
            AgentTeamStageRead(
                stage=stage.stage,
                status=stage.status,
                role_name=stage.role_name,
                display_name=(
                    role_definition(stage.role_name).display_name if stage.role_name is not None else None
                ),
                provider_status=stage.provider_status,
                unavailable_reason=stage.unavailable_reason,
            )
            for stage in state.stage_statuses
        ),
        safety_flags=state.safety_flags,
    )


def build_console_read_from_review_run_state(state: AgentReviewRunState) -> AgentTeamAnalysisConsoleRead:
    """Project the app-owned ``AgentReviewRunState`` onto the existing safe
    analysis-console contract (ADR 0008 spine; ADR 0009 backend-owned labels).

    Preserves ``AgentTeamAnalysisConsoleRead`` shape: machine ``role_name`` is
    unchanged, ``display_name`` comes from the role registry, ``run_status`` maps
    to the console vocabulary (``failed_safe`` -> ``failed``), and provider
    warnings are sanitized and provider-neutral (no raw provider payload, URL,
    key, exception body, or prompt trace).
    """

    return AgentTeamAnalysisConsoleRead(
        run_reference=state.run_reference,
        workflow_version=state.workflow_version,
        run_status=_REVIEW_RUN_STATUS_TO_CONSOLE.get(state.run_status, "failed"),
        generated_at=state.generated_at,
        review_flow_label=state.review_flow_label,
        review_actionability_status=state.review_actionability_status,
        broker_snapshot_freshness=state.broker_snapshot_freshness,
        market_quote_freshness=state.market_quote_freshness,
        deterministic_evidence_summary=_console_evidence_summary(state.deterministic_evidence_summary),
        scope_summary=_console_scope_summary(state.scope_summary),
        role_outputs=tuple(
            AgentTeamRoleOutputRead(
                role_name=output.role_name,
                display_name=role_definition(output.role_name).display_name,
                status=output.status,
                provider_status=output.provider_status,
                content_markdown=output.content_markdown,
                is_mock=output.is_mock,
                unavailable_reason=output.unavailable_reason,
            )
            for output in state.role_outputs
        ),
        final_synthesis=state.final_synthesis,
        provider_warnings=tuple(_provider_warning_read(warning) for warning in state.provider_warnings),
        stages=tuple(
            AgentTeamStageRead(
                stage=stage.stage,
                status=stage.status,
                role_name=stage.role_name,
                display_name=(
                    role_definition(stage.role_name).display_name if stage.role_name is not None else None
                ),
                provider_status=stage.provider_status,
                unavailable_reason=stage.unavailable_reason,
            )
            for stage in state.stage_statuses
        ),
        safety_flags=state.safety_flags,
    )


def _console_scope_summary(scope_summary: dict[str, object]) -> dict[str, object]:
    """Carry the lossy, sanitized scope summary onto the console contract.

    Falls back to an explicit 'unavailable' summary for run states constructed
    without scope (legacy/hand-built), so the console shape stays uniform. No
    account refs, labels, kinds, or balances are ever introduced here.
    """

    if scope_summary:
        return dict(scope_summary)
    return unavailable_agent_scope_summary()


def _console_evidence_summary(summary: dict[str, object]) -> dict[str, object]:
    """Keep the existing console deterministic-evidence shape (legacy
    ``stock_position_count`` key) without mutating the run-state's own summary."""

    console = dict(summary)
    shape = console.get("portfolio_shape")
    if isinstance(shape, dict) and "equity_position_count" in shape:
        legacy = dict(shape)
        legacy["stock_position_count"] = legacy.pop("equity_position_count")
        console["portfolio_shape"] = legacy
    return console


def _provider_warning_read(warning: str) -> AgentTeamProviderWarningRead:
    """Sanitized, provider-neutral console warning from a safe 'role:status' code."""

    role_name, _, status = warning.partition(":")
    status = status or "unavailable"
    display = role_definition(role_name).display_name if role_name in AGENT_TEAM_ROLES else role_name
    return AgentTeamProviderWarningRead(
        code=f"provider_role_{status}",
        message=f"{display} was unavailable ({status}); deterministic evidence remains available.",
    )
