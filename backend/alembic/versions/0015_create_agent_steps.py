"""create agent steps table

Revision ID: 0015_create_agent_steps
Revises: 0014_create_agent_runs
Create Date: 2026-05-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_create_agent_steps"
down_revision: str | None = "0014_create_agent_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("step_key", sa.String(length=120), nullable=False),
        sa.Column("step_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="queued", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("input_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("calculation_version", sa.String(length=80), nullable=True),
        sa.Column("data_freshness_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_run_id", "step_order", name="uq_agent_steps_run_order"),
    )
    op.create_index("ix_agent_steps_agent_run_id", "agent_steps", ["agent_run_id"], unique=False)
    op.create_index("ix_agent_steps_run_status", "agent_steps", ["agent_run_id", "status"], unique=False)
    op.create_index("ix_agent_steps_step_key", "agent_steps", ["step_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_steps_step_key", table_name="agent_steps")
    op.drop_index("ix_agent_steps_run_status", table_name="agent_steps")
    op.drop_index("ix_agent_steps_agent_run_id", table_name="agent_steps")
    op.drop_table("agent_steps")
