from fastapi import APIRouter

from app.schemas.trade_review_workspace import TradeReviewWorkspacePreviewRequest, TradeReviewWorkspaceRead
from app.services.trade_review.frontend_read import build_trade_review_workspace_preview

router = APIRouter(prefix="/trade-reviews", tags=["trade-reviews"])


@router.post("/preview", response_model=TradeReviewWorkspaceRead)
def preview_trade_review(payload: TradeReviewWorkspacePreviewRequest) -> TradeReviewWorkspaceRead:
    """Return a deterministic synthetic trade-review workspace preview."""

    return build_trade_review_workspace_preview(payload)
