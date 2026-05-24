from fastapi import APIRouter

from app.schemas.trade_review_workspace import (
    TradeReviewPortfolioPreviewRequest,
    TradeReviewWorkspacePreviewRequest,
    TradeReviewWorkspaceRead,
)
from app.services.trade_review.frontend_read import (
    build_trade_review_workspace_portfolio_preview,
    build_trade_review_workspace_preview,
)

router = APIRouter(prefix="/trade-reviews", tags=["trade-reviews"])


@router.post("/preview", response_model=TradeReviewWorkspaceRead)
def preview_trade_review(payload: TradeReviewWorkspacePreviewRequest) -> TradeReviewWorkspaceRead:
    """Return a deterministic synthetic trade-review workspace preview."""

    return build_trade_review_workspace_preview(payload)


@router.post("/portfolio-preview", response_model=TradeReviewWorkspaceRead)
def preview_portfolio_trade_review(payload: TradeReviewPortfolioPreviewRequest) -> TradeReviewWorkspaceRead:
    """Return a deterministic portfolio-backed trade-review workspace preview."""

    return build_trade_review_workspace_portfolio_preview(payload)
