from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BrokerConnection(Base):
    __tablename__ = "broker_connections"
    __table_args__ = (
        UniqueConstraint("provider", "provider_connection_id", name="uq_broker_connections_provider_connection"),
        Index("ix_broker_connections_user_provider_status", "user_id", "provider", "connection_status"),
        Index("ix_broker_connections_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    broker_name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_connection_id: Mapped[str] = mapped_column(String(160), nullable=False)
    connection_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="unknown",
        server_default="unknown",
    )
    sync_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="idle",
        server_default="idle",
    )
    data_freshness_status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="unknown",
        server_default="unknown",
    )
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempted_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    secret_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scopes: Mapped[list[str] | None] = mapped_column(ARRAY(String(80)), nullable=True)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
