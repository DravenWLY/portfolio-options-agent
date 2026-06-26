from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BrokerAccount(Base):
    __tablename__ = "broker_accounts"
    __table_args__ = (
        UniqueConstraint("broker_connection_id", "provider_account_id", name="uq_broker_accounts_connection_account"),
        Index("ix_broker_accounts_broker_connection_id", "broker_connection_id"),
        Index("ix_broker_accounts_account_id", "account_id"),
        Index("ix_broker_accounts_connection_freshness", "broker_connection_id", "data_freshness_status"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    broker_connection_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("broker_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    account_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    provider_account_id: Mapped[str] = mapped_column(String(160), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    user_nickname: Mapped[str | None] = mapped_column(String(60), nullable=True)
    account_type: Mapped[str] = mapped_column(String(40), nullable=False, default="other", server_default="other")
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
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
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
