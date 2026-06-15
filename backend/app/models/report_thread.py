from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportThread(Base):
    __tablename__ = "report_threads"
    __table_args__ = (
        Index("ix_report_threads_user_status", "user_id", "status"),
        Index("ix_report_threads_user_created_at", "user_id", "created_at"),
        Index("ix_report_threads_account_id", "account_id"),
        Index("ix_report_threads_deleted_at", "deleted_at"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    account_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="portfolio_report",
        server_default="portfolio_report",
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    saved_artifact_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def scope_metadata(self) -> dict | None:
        if not isinstance(self.saved_artifact_json, dict):
            return None
        scope = self.saved_artifact_json.get("scope_metadata")
        return scope if isinstance(scope, dict) else None

    @property
    def agent_summary(self) -> dict | None:
        if not isinstance(self.saved_artifact_json, dict):
            return None
        summary = self.saved_artifact_json.get("agent_summary")
        return summary if isinstance(summary, dict) else None
