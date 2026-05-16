from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.report_message import ReportMessage
from app.models.report_thread import ReportThread
from app.models.user import User
from app.schemas.reports import ReportMessageCreate, ReportThreadCreate


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
