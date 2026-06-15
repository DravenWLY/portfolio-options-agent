from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavedReviewSource(Base):
    __tablename__ = "saved_review_sources"
    __table_args__ = (
        UniqueConstraint("user_id", "source_kind", "source_reference", name="uq_saved_review_sources_user_source"),
        Index("ix_saved_review_sources_user_created_at", "user_id", "created_at"),
        Index("ix_saved_review_sources_source_reference", "source_reference"),
        Index("ix_saved_review_sources_deleted_at", "deleted_at"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(90), nullable=False)
    scope_metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    deterministic_summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    agent_summary_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    review_pipeline_label: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="Portfolio Copilot review pipeline",
        server_default="Portfolio Copilot review pipeline",
    )
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    caveat_codes_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
