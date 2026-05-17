from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProviderCredentialsMetadata(Base):
    __tablename__ = "provider_credentials_metadata"
    __table_args__ = (
        Index(
            "uq_provider_credentials_metadata_active_name",
            "user_id",
            "provider",
            "credential_name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_provider_credentials_metadata_user_provider", "user_id", "provider"),
        Index("ix_provider_credentials_metadata_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    credential_name: Mapped[str] = mapped_column(String(120), nullable=False)
    secret_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    encrypted_secret_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    scopes: Mapped[list[str] | None] = mapped_column(ARRAY(String(80)), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown", server_default="unknown")
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
