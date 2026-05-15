"""create broker connections table

Revision ID: 0008_create_broker_connections
Revises: 0007_create_option_positions
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_create_broker_connections"
down_revision: str | None = "0007_create_option_positions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broker_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("broker_name", sa.String(length=120), nullable=False),
        sa.Column("provider_connection_id", sa.String(length=160), nullable=False),
        sa.Column("connection_status", sa.String(length=40), server_default="unknown", nullable=False),
        sa.Column("sync_status", sa.String(length=40), server_default="idle", nullable=False),
        sa.Column("data_freshness_status", sa.String(length=40), server_default="unknown", nullable=False),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("secret_ref", sa.String(length=255), nullable=True),
        sa.Column("scopes", postgresql.ARRAY(sa.String(length=80)), nullable=True),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_connection_id", name="uq_broker_connections_provider_connection"),
    )
    op.create_index("ix_broker_connections_user_id", "broker_connections", ["user_id"], unique=False)
    op.create_index(
        "ix_broker_connections_user_provider_status",
        "broker_connections",
        ["user_id", "provider", "connection_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_broker_connections_user_provider_status", table_name="broker_connections")
    op.drop_index("ix_broker_connections_user_id", table_name="broker_connections")
    op.drop_table("broker_connections")
