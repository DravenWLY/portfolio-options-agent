from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import ConfigurationError, Settings, get_settings
from app.db.session import get_db
from app.schemas.reports import (
    PublicEvidencePreparationRead,
    ReportThreadCreate,
    ReportThreadDetailRead,
    ReportThreadRead,
    SavedReviewArtifactCreateRequest,
    SavedReviewArtifactRead,
)
from app.services.reports import crud as report_service
from app.services.reports import agent_team_report as agent_team_report_service
from app.services.reports.public_evidence import (
    EdgarCompanyProfileClient,
    EdgarCompanyProfileSourcePolicy,
    EdgarRecentFilingsClient,
    EdgarRecentFilingsSourcePolicy,
    resolve_edgar_report_evidence_from_settings,
)
from app.services.market_data.eod_history import (
    MarketContextExecutionContext,
    MarketContextPolicy,
    default_market_context_execution_context,
    market_context_policy_from_environment,
)
from app.services.reports.source_snapshots import (
    FmpFundamentalsClient,
    FmpFundamentalsExecutionContext,
    FmpFundamentalsHttpClient,
    FmpFundamentalsSourcePolicy,
    UtcDayRequestBudget,
    fmp_fundamentals_execution_context_for_client,
    fmp_fundamentals_policy_from_settings,
)

router = APIRouter(tags=["reports"])

# Compatibility seam for fixture tests that assert Skyframe POST interception
# happens before saved-report generation can reach the real service.
generate_agent_team_report_for_thread = agent_team_report_service.generate_agent_team_report_for_thread


def _resolve_fmp_eod_history_generation_context() -> tuple[
    MarketContextPolicy | None,
    MarketContextExecutionContext | None,
]:
    """Resolve the approved EOD lane only when its existing live config is complete."""

    policy = market_context_policy_from_environment()
    if not policy.live_enabled:
        return None, None
    try:
        return policy, default_market_context_execution_context()
    except ConfigurationError:
        # A live mode without the backend-only FMP credential remains disabled.
        return None, None


def _resolve_fmp_fundamentals_generation_context(
    *,
    settings: Settings | None = None,
    client_factory: Callable[..., FmpFundamentalsClient] | None = None,
) -> tuple[FmpFundamentalsSourcePolicy | None, FmpFundamentalsExecutionContext | None]:
    """Resolve the approved fundamentals lane only for complete live config."""

    try:
        active_settings = settings or get_settings()
        policy = fmp_fundamentals_policy_from_settings(active_settings)
    except (ConfigurationError, TypeError, ValueError):
        return None, None
    if not policy.live_client_ready():
        return None, None

    factory = client_factory or FmpFundamentalsHttpClient
    try:
        client = factory(api_key=active_settings.require_fmp_api_key())
        context = fmp_fundamentals_execution_context_for_client(
            client,
            daily_budget=UtcDayRequestBudget(policy.daily_request_budget),
        )
    except Exception:
        # Client construction is configuration-only here. Fail closed before
        # the report builder can make a source request.
        return None, None
    return policy, context


def _resolve_edgar_report_evidence_generation_context() -> tuple[
    EdgarCompanyProfileSourcePolicy | None,
    EdgarCompanyProfileClient | None,
    EdgarRecentFilingsSourcePolicy | None,
    EdgarRecentFilingsClient | None,
]:
    """Resolve both approved EDGAR report lanes without partial activation."""

    resolution = resolve_edgar_report_evidence_from_settings()
    return (
        resolution.company_profile_policy,
        resolution.company_profile_client,
        resolution.recent_filings_policy,
        resolution.recent_filings_client,
    )


@router.post("/users/{user_id}/reports", response_model=ReportThreadRead, status_code=status.HTTP_201_CREATED)
def create_report_thread(user_id: UUID, payload: ReportThreadCreate, db: Session = Depends(get_db)) -> ReportThreadRead:
    report_thread = report_service.create_report_thread(db, user_id, payload)
    if report_thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or account not found")
    return report_thread


@router.post(
    "/users/{user_id}/reports/from-trade-review",
    response_model=SavedReviewArtifactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_report_from_trade_review(
    user_id: UUID,
    payload: SavedReviewArtifactCreateRequest,
    db: Session = Depends(get_db),
) -> SavedReviewArtifactRead:
    saved_artifact = report_service.create_saved_review_artifact(db, user_id, payload)
    if saved_artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved review source not found")
    return saved_artifact


@router.post(
    "/users/{user_id}/reports/{thread_id}/prepare-evidence",
    response_model=PublicEvidencePreparationRead,
    status_code=status.HTTP_200_OK,
)
def prepare_report_public_evidence(
    user_id: UUID,
    thread_id: UUID,
    db: Session = Depends(get_db),
) -> PublicEvidencePreparationRead:
    fmp_eod_history_policy, fmp_eod_history_context = _resolve_fmp_eod_history_generation_context()
    fmp_fundamentals_policy, fmp_fundamentals_context = _resolve_fmp_fundamentals_generation_context()
    (
        edgar_policy,
        edgar_client,
        edgar_recent_filings_policy,
        edgar_recent_filings_client,
    ) = _resolve_edgar_report_evidence_generation_context()
    readiness = agent_team_report_service.prepare_public_evidence_for_thread(
        db,
        user_id,
        thread_id,
        edgar_policy=edgar_policy,
        edgar_client=edgar_client,
        edgar_recent_filings_policy=edgar_recent_filings_policy,
        edgar_recent_filings_client=edgar_recent_filings_client,
        fmp_eod_history_policy=fmp_eod_history_policy,
        fmp_eod_history_context=fmp_eod_history_context,
        fmp_fundamentals_policy=fmp_fundamentals_policy,
        fmp_fundamentals_context=fmp_fundamentals_context,
    )
    if readiness is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved review artifact not found")
    return readiness


@router.post(
    "/users/{user_id}/reports/{thread_id}/agent-team-report",
    response_model=SavedReviewArtifactRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_report_agent_team_summary(
    user_id: UUID,
    thread_id: UUID,
    db: Session = Depends(get_db),
) -> SavedReviewArtifactRead:
    generation_mode = agent_team_report_service.resolve_backend_agent_team_report_generation_mode()
    if generation_mode == "tool_mediated":
        provider_resolution = agent_team_report_service.resolve_agent_team_report_provider_resolution()
        p36_risk_live_enabled, p36_public_live_enabled, p36_pm_live_enabled = (
            agent_team_report_service.resolve_p36_live_lane_flags()
        )
    else:
        provider_resolution = None
        p36_risk_live_enabled = False
        p36_public_live_enabled = False
        p36_pm_live_enabled = False
    fmp_eod_history_policy, fmp_eod_history_context = _resolve_fmp_eod_history_generation_context()
    fmp_fundamentals_policy, fmp_fundamentals_context = _resolve_fmp_fundamentals_generation_context()
    (
        edgar_policy,
        edgar_client,
        edgar_recent_filings_policy,
        edgar_recent_filings_client,
    ) = _resolve_edgar_report_evidence_generation_context()
    agent_summary = agent_team_report_service.generate_agent_team_report_for_thread(
        db,
        user_id,
        thread_id,
        mode=generation_mode,
        provider_resolution=provider_resolution,
        p36_risk_live_enabled=p36_risk_live_enabled,
        p36_public_live_enabled=p36_public_live_enabled,
        p36_pm_live_enabled=p36_pm_live_enabled,
        edgar_policy=edgar_policy,
        edgar_client=edgar_client,
        edgar_recent_filings_policy=edgar_recent_filings_policy,
        edgar_recent_filings_client=edgar_recent_filings_client,
        fmp_eod_history_policy=fmp_eod_history_policy,
        fmp_eod_history_context=fmp_eod_history_context,
        fmp_fundamentals_policy=fmp_fundamentals_policy,
        fmp_fundamentals_context=fmp_fundamentals_context,
    )
    if agent_summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved review artifact not found")
    report_thread = report_service.get_report_thread(db, user_id, thread_id)
    if report_thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved review artifact not found")
    return report_service.saved_review_artifact_for_thread(report_thread)


@router.get("/users/{user_id}/reports", response_model=list[ReportThreadRead])
def list_report_threads(user_id: UUID, db: Session = Depends(get_db)) -> list[ReportThreadRead]:
    report_threads = report_service.list_report_threads(db, user_id)
    if report_threads is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return report_threads


@router.get("/users/{user_id}/reports/{thread_id}", response_model=ReportThreadDetailRead)
def get_report_thread(user_id: UUID, thread_id: UUID, db: Session = Depends(get_db)) -> ReportThreadDetailRead:
    report_thread = report_service.get_report_thread(db, user_id, thread_id)
    if report_thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report thread not found")
    base_thread = ReportThreadRead.model_validate(report_thread)
    return ReportThreadDetailRead(
        **base_thread.model_dump(),
        messages=report_service.list_report_messages(db, report_thread.id),
    )
