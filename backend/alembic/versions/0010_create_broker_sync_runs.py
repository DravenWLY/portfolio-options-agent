"""create broker sync runs table

Revision ID: 0010_create_broker_sync_runs
Revises: 0009_create_broker_accounts
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_create_broker_sync_runs"
down_revision: str | None = "0009_create_broker_accounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broker_sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("broker_connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("broker_account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trigger", sa.String(length=40), server_default="manual", nullable=False),
        sa.Column("status", sa.String(length=40), server_default="queued", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_request_id", sa.String(length=160), nullable=True),
        sa.Column("accounts_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("positions_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("transactions_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["broker_account_id"], ["broker_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["broker_connection_id"], ["broker_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_broker_sync_runs_connection_started",
        "broker_sync_runs",
        ["broker_connection_id", "started_at"],
        unique=False,
    )
    op.create_index("ix_broker_sync_runs_broker_account_id", "broker_sync_runs", ["broker_account_id"], unique=False)
    op.create_index("ix_broker_sync_runs_status", "broker_sync_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_broker_sync_runs_status", table_name="broker_sync_runs")
    op.drop_index("ix_broker_sync_runs_broker_account_id", table_name="broker_sync_runs")
    op.drop_index("ix_broker_sync_runs_connection_started", table_name="broker_sync_runs")
    op.drop_table("broker_sync_runs")
