from fastapi import APIRouter

from app.schemas.agent_team import AgentTeamAnalysisConsoleRead, AgentTeamAnalysisPreviewRequest
from app.services.agent_team.frontend_read import build_agent_team_analysis_console_read
from app.services.agent_team.orchestrator import AgentTeamOrchestrator
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview

router = APIRouter(prefix="/agent-team", tags=["agent-team"])


@router.post("/trade-review-analysis/preview", response_model=AgentTeamAnalysisConsoleRead)
def preview_agent_team_trade_review_analysis(
    payload: AgentTeamAnalysisPreviewRequest,
) -> AgentTeamAnalysisConsoleRead:
    """Return a stateless mock-provider agent-team analysis console preview."""

    workspace = build_trade_review_workspace_portfolio_preview(payload)
    state = AgentTeamOrchestrator().run(workspace=workspace)
    return build_agent_team_analysis_console_read(state)
