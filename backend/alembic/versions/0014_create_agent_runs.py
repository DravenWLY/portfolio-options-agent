"""create agent runs table

Revision ID: 0014_create_agent_runs
Revises: 0013_create_report_messages
Create Date: 2026-05-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_create_agent_runs"
down_revision: str | None = "0013_create_report_messages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_thread_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_type", sa.String(length=80), server_default="portfolio_analysis", nullable=False),
        sa.Column("status", sa.String(length=40), server_default="queued", nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("token_budget", sa.Integer(), nullable=True),
        sa.Column("cost_budget", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("input_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("calculation_version", sa.String(length=80), nullable=True),
        sa.Column("data_freshness_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["report_thread_id"], ["report_threads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_runs_report_thread_id", "agent_runs", ["report_thread_id"], unique=False)
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"], unique=False)
    op.create_index("ix_agent_runs_user_account", "agent_runs", ["user_id", "account_id"], unique=False)
    op.create_index("ix_agent_runs_user_created_at", "agent_runs", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_runs_user_created_at", table_name="agent_runs")
    op.drop_index("ix_agent_runs_user_account", table_name="agent_runs")
    op.drop_index("ix_agent_runs_status", table_name="agent_runs")
    op.drop_index("ix_agent_runs_report_thread_id", table_name="agent_runs")
    op.drop_table("agent_runs")
