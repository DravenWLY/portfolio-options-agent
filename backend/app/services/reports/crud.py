from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.models.account import Account
from app.models.report_message import ReportMessage
from app.models.report_thread import ReportThread
from app.models.saved_review_source import SavedReviewSource
from app.models.user import User
from app.schemas.reports import (
    ReportMessageCreate,
    ReportThreadCreate,
    SavedAgentTeamSummaryRead,
    SavedDeterministicReviewSummaryRead,
    SavedReviewArtifactCreateRequest,
    SavedReviewArtifactRead,
    SavedReviewReportMetadataRead,
)
from app.schemas.trade_review_workspace import ReportScopeMetadataRead


def _user_exists(db: Session, user_id: UUID) -> bool:
    return db.scalar(select(User.id).where(User.id == user_id, User.deleted_at.is_(None))) is not None


def _account_belongs_to_user(db: Session, user_id: UUID, account_id: UUID) -> bool:
    return (
        db.scalar(
            select(Account.id).where(
                Account.id == account_id,
                Account.user_id == user_id,
                Account.deleted_at.is_(None),
            )
        )
        is not None
    )


def create_report_thread(db: Session, user_id: UUID, payload: ReportThreadCreate) -> ReportThread | None:
    if not _user_exists(db, user_id):
        return None
    if payload.account_id is not None and not _account_belongs_to_user(db, user_id, payload.account_id):
        return None

    report_thread = ReportThread(
        user_id=user_id,
        account_id=payload.account_id,
        title=payload.title,
        report_type=payload.report_type,
        status=payload.status,
    )
    db.add(report_thread)
    db.commit()
    db.refresh(report_thread)
    return report_thread


def create_saved_review_artifact(
    db: Session,
    user_id: UUID,
    payload: SavedReviewArtifactCreateRequest,
) -> SavedReviewArtifactRead | None:
    if not _user_exists(db, user_id):
        return None
    if payload.source_kind != "trade_review_workspace":
        return None

    source = _get_saved_review_source(
        db,
        user_id=user_id,
        source_kind=payload.source_kind,
        source_reference=payload.source_reference,
    )
    if source is None:
        return None

    saved_at = datetime.now(UTC)
    artifact_reference = f"svrev_{uuid4().hex}"
    saved_artifact_json = {
        "artifact_reference": artifact_reference,
        "source_kind": source.source_kind,
        "source_reference": source.source_reference,
        "scope_metadata": source.scope_metadata_json,
        "deterministic_summary": source.deterministic_summary_json,
        "agent_summary": source.agent_summary_json,
        "generated_at": source.generated_at.isoformat(),
        "saved_at": saved_at.isoformat(),
        "review_pipeline_label": source.review_pipeline_label,
        "limitations": source.limitations_json,
        "caveat_codes": source.caveat_codes_json,
    }
    if not _saved_artifact_json_can_be_committed(
        saved_artifact_json,
        title=payload.title,
        report_type=payload.report_type,
        status="completed",
        created_at=saved_at,
        updated_at=saved_at,
    ):
        return None
    report_thread = ReportThread(
        user_id=user_id,
        account_id=None,
        title=payload.title,
        report_type=payload.report_type,
        status="completed",
        saved_artifact_json=saved_artifact_json,
    )
    db.add(report_thread)
    db.commit()
    db.refresh(report_thread)
    return saved_review_artifact_for_thread(report_thread)


def record_saved_review_source(
    db: Session,
    user_id: UUID,
    payload: SavedReviewArtifactCreateRequest,
) -> SavedReviewSource | None:
    """Persist a reviewed, sanitized source snapshot for later saved-artifact creation.

    This is an internal backend boundary for completed review pipelines. The
    public save endpoint resolves against these rows instead of trusting client
    supplied scope or summary data.
    """

    if not _user_exists(db, user_id):
        return None
    if payload.scope_metadata is None or payload.deterministic_summary is None:
        return None

    generated_at = payload.generated_at or datetime.now(UTC)
    source = SavedReviewSource(
        user_id=user_id,
        source_kind=payload.source_kind,
        source_reference=payload.source_reference,
        scope_metadata_json=payload.scope_metadata.model_dump(mode="json"),
        deterministic_summary_json=payload.deterministic_summary.model_dump(mode="json"),
        agent_summary_json=payload.agent_summary.model_dump(mode="json") if payload.agent_summary is not None else None,
        generated_at=generated_at,
        review_pipeline_label=payload.review_pipeline_label,
        limitations_json=list(payload.limitations),
        caveat_codes_json=list(payload.caveat_codes),
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def saved_review_artifact_for_thread(report_thread: ReportThread) -> SavedReviewArtifactRead:
    saved_artifact_json = report_thread.saved_artifact_json or {}
    artifact_reference = saved_artifact_json.get("artifact_reference") or f"svrev_{report_thread.id.hex}"
    generated_at = saved_artifact_json.get("generated_at") or report_thread.created_at
    saved_at = saved_artifact_json.get("saved_at") or report_thread.created_at
    return SavedReviewArtifactRead(
        artifact_reference=artifact_reference,
        source_kind=saved_artifact_json.get("source_kind"),
        source_reference=saved_artifact_json.get("source_reference"),
        status="saved" if saved_artifact_json else "unavailable",
        report=SavedReviewReportMetadataRead(
            report_reference=artifact_reference,
            title=report_thread.title,
            report_type=report_thread.report_type,
            status=report_thread.status,
            created_at=report_thread.created_at,
            updated_at=report_thread.updated_at,
        ),
        scope_metadata=saved_artifact_json.get("scope_metadata"),
        deterministic_summary=saved_artifact_json.get("deterministic_summary"),
        agent_summary=saved_artifact_json.get("agent_summary"),
        generated_at=generated_at,
        saved_at=saved_at,
        review_pipeline_label=saved_artifact_json.get("review_pipeline_label")
        or "Portfolio Copilot review pipeline",
        limitations=tuple(saved_artifact_json.get("limitations") or ()),
        caveat_codes=tuple(saved_artifact_json.get("caveat_codes") or ()),
    )


def _get_saved_review_source(
    db: Session,
    *,
    user_id: UUID,
    source_kind: str,
    source_reference: str,
) -> SavedReviewSource | None:
    source = db.scalar(
        select(SavedReviewSource).where(
            SavedReviewSource.user_id == user_id,
            SavedReviewSource.source_kind == source_kind,
            SavedReviewSource.source_reference == source_reference,
            SavedReviewSource.deleted_at.is_(None),
        )
    )
    if source is None:
        return None
    if not _saved_review_source_payload_is_valid(source):
        return None
    return source


def _saved_artifact_json_can_be_committed(
    saved_artifact_json: dict,
    *,
    title: str,
    report_type: str,
    status: str,
    created_at: datetime,
    updated_at: datetime,
) -> bool:
    try:
        SavedReviewArtifactRead(
            artifact_reference=saved_artifact_json["artifact_reference"],
            source_kind=saved_artifact_json.get("source_kind"),
            source_reference=saved_artifact_json.get("source_reference"),
            status="saved",
            report=SavedReviewReportMetadataRead(
                report_reference=saved_artifact_json["artifact_reference"],
                title=title,
                report_type=report_type,
                status=status,
                created_at=created_at,
                updated_at=updated_at,
            ),
            scope_metadata=saved_artifact_json.get("scope_metadata"),
            deterministic_summary=saved_artifact_json.get("deterministic_summary"),
            agent_summary=saved_artifact_json.get("agent_summary"),
            generated_at=saved_artifact_json.get("generated_at"),
            saved_at=saved_artifact_json.get("saved_at"),
            review_pipeline_label=saved_artifact_json.get("review_pipeline_label"),
            limitations=saved_artifact_json.get("limitations") or (),
            caveat_codes=saved_artifact_json.get("caveat_codes") or (),
        )
    except (KeyError, TypeError, ValidationError, ValueError):
        return False
    return True


def _saved_review_source_payload_is_valid(source: SavedReviewSource) -> bool:
    if not isinstance(source.scope_metadata_json, dict) or not isinstance(source.deterministic_summary_json, dict):
        return False
    if source.agent_summary_json is not None and not isinstance(source.agent_summary_json, dict):
        return False
    try:
        ReportScopeMetadataRead.model_validate(source.scope_metadata_json)
        SavedDeterministicReviewSummaryRead.model_validate(source.deterministic_summary_json)
        if source.agent_summary_json is not None:
            SavedAgentTeamSummaryRead.model_validate(source.agent_summary_json)
    except (TypeError, ValidationError, ValueError):
        return False
    return True


def list_report_threads(db: Session, user_id: UUID) -> list[ReportThread] | None:
    if not _user_exists(db, user_id):
        return None

    return list(
        db.scalars(
            select(ReportThread)
            .where(ReportThread.user_id == user_id, ReportThread.deleted_at.is_(None))
            .order_by(ReportThread.created_at.desc(), ReportThread.id.desc())
        )
    )


def get_report_thread(db: Session, user_id: UUID, thread_id: UUID) -> ReportThread | None:
    return db.scalar(
        select(ReportThread).where(
            ReportThread.id == thread_id,
            ReportThread.user_id == user_id,
            ReportThread.deleted_at.is_(None),
        )
    )


def list_report_messages(db: Session, thread_id: UUID) -> list[ReportMessage]:
    return list(
        db.scalars(
            select(ReportMessage)
            .where(ReportMessage.thread_id == thread_id, ReportMessage.deleted_at.is_(None))
            .order_by(ReportMessage.sequence.asc(), ReportMessage.id.asc())
        )
    )


def next_message_sequence(db: Session, thread_id: UUID) -> int:
    max_sequence = db.scalar(select(func.max(ReportMessage.sequence)).where(ReportMessage.thread_id == thread_id))
    return (max_sequence or 0) + 1


def create_report_message(db: Session, thread_id: UUID, payload: ReportMessageCreate) -> ReportMessage:
    message = ReportMessage(
        thread_id=thread_id,
        sender_type=payload.sender_type,
        message_type=payload.message_type,
        content_markdown=payload.content_markdown,
        content_json=payload.content_json,
        sequence=payload.sequence,
        visibility=payload.visibility,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
