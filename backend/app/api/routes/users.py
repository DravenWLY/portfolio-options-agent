from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.trade_review_workspace import (
    DashboardAccountSummaryRead,
    PortfolioContextDetailRead,
    PortfolioContextListRead,
    ReviewReadinessRead,
    RiskAlertListRead,
    TradeReviewListRead,
)
from app.schemas.user import UserCreate, UserRead
from app.services import users as user_service
from app.services.trade_review.frontend_read import (
    get_dashboard_account_summary_for_user,
    get_latest_portfolio_context_for_user,
    get_portfolio_context_for_user,
    get_review_readiness_for_user,
    list_portfolio_contexts_for_user,
    list_recent_trade_reviews_for_user,
    list_risk_alerts_for_user,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    return user_service.create_user(db, payload)


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[UserRead]:
    return user_service.list_users(db)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/{user_id}/trade-reviews", response_model=TradeReviewListRead)
def list_user_trade_reviews(user_id: UUID) -> TradeReviewListRead:
    """Return a sanitized recent trade-review list for a user."""

    return list_recent_trade_reviews_for_user(user_id)


@router.get("/{user_id}/risk-alerts", response_model=RiskAlertListRead)
def list_user_risk_alerts(user_id: UUID) -> RiskAlertListRead:
    """Return sanitized aggregate risk-alert cards for a user."""

    return list_risk_alerts_for_user(user_id)


@router.get("/{user_id}/readiness", response_model=ReviewReadinessRead)
def get_user_readiness(user_id: UUID) -> ReviewReadinessRead:
    """Return a sanitized aggregate review-readiness summary for a user."""

    return get_review_readiness_for_user(user_id)


@router.get("/{user_id}/dashboard-account-summary", response_model=DashboardAccountSummaryRead)
def get_user_dashboard_account_summary(user_id: UUID) -> DashboardAccountSummaryRead:
    """Return a sanitized Dashboard account-summary contract for a user."""

    return get_dashboard_account_summary_for_user(user_id)


@router.get("/{user_id}/portfolio-contexts", response_model=PortfolioContextListRead)
def list_user_portfolio_contexts(user_id: UUID) -> PortfolioContextListRead:
    """Return sanitized standalone portfolio-context cards for a user."""

    return list_portfolio_contexts_for_user(user_id)


@router.get("/{user_id}/portfolio-context/latest", response_model=PortfolioContextDetailRead)
def get_user_latest_portfolio_context(user_id: UUID) -> PortfolioContextDetailRead:
    """Return the latest sanitized portfolio-context detail for a user."""

    return get_latest_portfolio_context_for_user(user_id)


@router.get("/{user_id}/portfolio-context/{context_reference}", response_model=PortfolioContextDetailRead)
def get_user_portfolio_context(user_id: UUID, context_reference: str) -> PortfolioContextDetailRead:
    """Return one sanitized portfolio-context detail by opaque reference."""

    try:
        return get_portfolio_context_for_user(user_id, context_reference)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio context not found") from exc
