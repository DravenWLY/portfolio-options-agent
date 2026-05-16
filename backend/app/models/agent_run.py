from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_status", "status"),
        Index("ix_agent_runs_user_account", "user_id", "account_id"),
        Index("ix_agent_runs_report_thread_id", "report_thread_id"),
        Index("ix_agent_runs_user_created_at", "user_id", "created_at"),
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
    report_thread_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("report_threads.id", ondelete="SET NULL"),
        nullable=True,
    )
    run_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="portfolio_analysis",
        server_default="portfolio_analysis",
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="queued", server_default="queued")
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    token_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    input_snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    calculation_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    data_freshness_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
