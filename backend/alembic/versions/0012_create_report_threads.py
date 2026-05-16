"""create report threads table

Revision ID: 0012_create_report_threads
Revises: 0011_provider_credentials
Create Date: 2026-05-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_create_report_threads"
down_revision: str | None = "0011_provider_credentials"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("report_type", sa.String(length=80), server_default="portfolio_report", nullable=False),
        sa.Column("status", sa.String(length=40), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_threads_account_id", "report_threads", ["account_id"], unique=False)
    op.create_index("ix_report_threads_deleted_at", "report_threads", ["deleted_at"], unique=False)
    op.create_index("ix_report_threads_user_created_at", "report_threads", ["user_id", "created_at"], unique=False)
    op.create_index("ix_report_threads_user_status", "report_threads", ["user_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_report_threads_user_status", table_name="report_threads")
    op.drop_index("ix_report_threads_user_created_at", table_name="report_threads")
    op.drop_index("ix_report_threads_deleted_at", table_name="report_threads")
    op.drop_index("ix_report_threads_account_id", table_name="report_threads")
    op.drop_table("report_threads")
