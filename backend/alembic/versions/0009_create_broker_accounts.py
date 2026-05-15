"""create broker accounts table

Revision ID: 0009_create_broker_accounts
Revises: 0008_create_broker_connections
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_create_broker_accounts"
down_revision: str | None = "0008_create_broker_connections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broker_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("broker_connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider_account_id", sa.String(length=160), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("account_type", sa.String(length=40), server_default="other", nullable=False),
        sa.Column("base_currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("sync_status", sa.String(length=40), server_default="idle", nullable=False),
        sa.Column("data_freshness_status", sa.String(length=40), server_default="unknown", nullable=False),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["broker_connection_id"], ["broker_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("broker_connection_id", "provider_account_id", name="uq_broker_accounts_connection_account"),
    )
    op.create_index("ix_broker_accounts_account_id", "broker_accounts", ["account_id"], unique=False)
    op.create_index(
        "ix_broker_accounts_broker_connection_id",
        "broker_accounts",
        ["broker_connection_id"],
        unique=False,
    )
    op.create_index(
        "ix_broker_accounts_connection_freshness",
        "broker_accounts",
        ["broker_connection_id", "data_freshness_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_broker_accounts_connection_freshness", table_name="broker_accounts")
    op.drop_index("ix_broker_accounts_broker_connection_id", table_name="broker_accounts")
    op.drop_index("ix_broker_accounts_account_id", table_name="broker_accounts")
    op.drop_table("broker_accounts")
