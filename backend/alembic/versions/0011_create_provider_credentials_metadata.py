"""create provider credentials metadata table

Revision ID: 0011_provider_credentials
Revises: 0010_create_broker_sync_runs
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_provider_credentials"
down_revision: str | None = "0010_create_broker_sync_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_credentials_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("credential_name", sa.String(length=120), nullable=False),
        sa.Column("secret_ref", sa.String(length=255), nullable=True),
        sa.Column("encrypted_secret_ref", sa.String(length=255), nullable=True),
        sa.Column("scopes", postgresql.ARRAY(sa.String(length=80)), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="unknown", nullable=False),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_provider_credentials_metadata_status",
        "provider_credentials_metadata",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_provider_credentials_metadata_user_provider",
        "provider_credentials_metadata",
        ["user_id", "provider"],
        unique=False,
    )
    op.create_index(
        "uq_provider_credentials_metadata_active_name",
        "provider_credentials_metadata",
        ["user_id", "provider", "credential_name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_provider_credentials_metadata_active_name", table_name="provider_credentials_metadata")
    op.drop_index("ix_provider_credentials_metadata_user_provider", table_name="provider_credentials_metadata")
    op.drop_index("ix_provider_credentials_metadata_status", table_name="provider_credentials_metadata")
    op.drop_table("provider_credentials_metadata")
