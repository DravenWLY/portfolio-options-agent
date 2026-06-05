from fastapi import APIRouter

from app.schemas.agent_team import AgentTeamAnalysisConsoleRead, AgentTeamAnalysisPreviewRequest
from app.services.agent_team.frontend_read import build_console_read_from_review_run_state
from app.services.agent_team.review_runner import ReviewRunner
from app.services.trade_review.frontend_read import build_trade_review_workspace_portfolio_preview

router = APIRouter(prefix="/agent-team", tags=["agent-team"])


@router.post("/trade-review-analysis/preview", response_model=AgentTeamAnalysisConsoleRead)
def preview_agent_team_trade_review_analysis(
    payload: AgentTeamAnalysisPreviewRequest,
) -> AgentTeamAnalysisConsoleRead:
    """Return a stateless, read-only agent-team analysis console preview.

    Runs the reviewed ``ReviewRunner`` spine (safety/eval/timing/budget) with the
    backend-resolved provider (mock by default; live only via backend env config,
    never frontend selection). The Agent Console composer stays disabled; this is
    a read-only analysis report.
    """

    workspace = build_trade_review_workspace_portfolio_preview(payload)
    state = ReviewRunner().run(workspace=workspace)
    return build_console_read_from_review_run_state(state)
