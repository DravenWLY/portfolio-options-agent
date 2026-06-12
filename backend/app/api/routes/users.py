from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.routes.broker_sync import get_snaptrade_adapter
from app.db.session import get_db
from app.schemas.trade_review_workspace import (
    AccountDetailsRead,
    AccountDetailsSyncRead,
    DashboardAccountSummaryRead,
    PortfolioContextDetailRead,
    PortfolioContextListRead,
    ReviewReadinessRead,
    RiskAlertListRead,
    SelectedAccountDetailsRead,
    TradeReviewListRead,
)
from app.schemas.user import UserCreate, UserRead
from app.services import users as user_service
from app.services.broker_import import sync as broker_sync_service
from app.services.broker_import.providers.snaptrade import SnapTradeAdapter
from app.services.trade_review.frontend_read import (
    get_account_details_for_user,
    get_dashboard_account_summary_for_user,
    get_latest_portfolio_context_for_user,
    get_portfolio_context_for_user,
    get_review_readiness_for_user,
    get_selected_account_details_for_user,
    list_portfolio_contexts_for_user,
    list_recent_trade_reviews_for_user,
    list_risk_alerts_for_user,
    resolve_broker_account_id_for_account_details_sync,
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


@router.get("/{user_id}/account-details", response_model=AccountDetailsRead)
def get_user_account_details(user_id: UUID, db: Session = Depends(get_db)) -> AccountDetailsRead:
    """Return sanitized Account Details rows and portfolio-scope metadata."""

    return get_account_details_for_user(user_id, db=db)


@router.get("/{user_id}/account-details/{account_reference}", response_model=SelectedAccountDetailsRead)
def get_user_selected_account_details(
    user_id: UUID,
    account_reference: str,
    db: Session = Depends(get_db),
) -> SelectedAccountDetailsRead:
    """Return sanitized display rows for one selected account."""

    try:
        return get_selected_account_details_for_user(user_id, account_reference, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account details not found") from exc


@router.post(
    "/{user_id}/account-details/{account_reference}/sync",
    response_model=AccountDetailsSyncRead,
    status_code=status.HTTP_201_CREATED,
)
def sync_user_selected_account_details(
    user_id: UUID,
    account_reference: str,
    db: Session = Depends(get_db),
    adapter: SnapTradeAdapter = Depends(get_snaptrade_adapter),
) -> AccountDetailsSyncRead:
    """Refresh one selected account via its opaque Account Details reference."""

    try:
        broker_account_id = resolve_broker_account_id_for_account_details_sync(
            user_id,
            account_reference,
            db=db,
        )
        sync_run = broker_sync_service.sync_broker_account(
            db,
            user_id,
            broker_account_id,
            adapter,
            trigger="manual",
        )
    except (ValueError, LookupError, broker_sync_service.BrokerSyncAccountNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account details not found") from None
    except broker_sync_service.ActiveBrokerSyncRunError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "account_reference": account_reference,
                "status": "running",
                "message": "Account sync already in progress.",
                "generated_at": datetime.now(UTC).isoformat(),
                "started_at": None,
                "completed_at": None,
            },
        )
    except RuntimeError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Broker provider request failed") from None

    return AccountDetailsSyncRead(
        account_reference=account_reference,
        status=sync_run.status,
        message=_account_details_sync_message(sync_run.status),
        generated_at=datetime.now(UTC),
        started_at=sync_run.started_at,
        completed_at=sync_run.completed_at,
    )


def _account_details_sync_message(sync_status: str) -> str:
    if sync_status == "succeeded":
        return "Account sync completed."
    if sync_status == "partially_succeeded":
        return "Account sync completed with some unavailable data."
    if sync_status == "failed":
        return "Account sync failed."
    return "Account sync status updated."


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
