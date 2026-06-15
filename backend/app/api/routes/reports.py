from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reports import (
    ReportThreadCreate,
    ReportThreadDetailRead,
    ReportThreadRead,
    SavedReviewArtifactCreateRequest,
    SavedReviewArtifactRead,
)
from app.services.reports import crud as report_service
from app.services.reports.agent_team_report import generate_agent_team_report_for_thread

router = APIRouter(tags=["reports"])


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
    "/users/{user_id}/reports/{thread_id}/agent-team-report",
    response_model=SavedReviewArtifactRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_report_agent_team_summary(
    user_id: UUID,
    thread_id: UUID,
    db: Session = Depends(get_db),
) -> SavedReviewArtifactRead:
    agent_summary = generate_agent_team_report_for_thread(db, user_id, thread_id)
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
