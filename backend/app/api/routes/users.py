from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.trade_review_workspace import ReviewReadinessRead, RiskAlertListRead, TradeReviewListRead
from app.schemas.user import UserCreate, UserRead
from app.services import users as user_service
from app.services.trade_review.frontend_read import (
    get_review_readiness_for_user,
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
