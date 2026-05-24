"""Frontend/API read projection for the Phase 19A analysis console."""

from app.schemas.agent_team import (
    AgentTeamAnalysisConsoleRead,
    AgentTeamProviderWarningRead,
    AgentTeamRoleOutputRead,
    AgentTeamStageRead,
)
from app.services.agent_team.state import AgentTeamAnalysisState


def build_agent_team_analysis_console_read(state: AgentTeamAnalysisState) -> AgentTeamAnalysisConsoleRead:
    """Map internal agent-team state to the safe analysis-console contract."""

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
        role_outputs=tuple(
            AgentTeamRoleOutputRead(
                role_name=output.role_name,
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
                provider_status=stage.provider_status,
                unavailable_reason=stage.unavailable_reason,
            )
            for stage in state.stage_statuses
        ),
        safety_flags=state.safety_flags,
    )
