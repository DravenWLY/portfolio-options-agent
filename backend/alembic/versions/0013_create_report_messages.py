"""create report messages table

Revision ID: 0013_create_report_messages
Revises: 0012_create_report_threads
Create Date: 2026-05-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_create_report_messages"
down_revision: str | None = "0012_create_report_threads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_type", sa.String(length=40), nullable=False),
        sa.Column("message_type", sa.String(length=40), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=True),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("visibility", sa.String(length=40), server_default="private", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["thread_id"], ["report_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id", "sequence", name="uq_report_messages_thread_sequence"),
    )
    op.create_index("ix_report_messages_deleted_at", "report_messages", ["deleted_at"], unique=False)
    op.create_index("ix_report_messages_message_type", "report_messages", ["message_type"], unique=False)
    op.create_index("ix_report_messages_thread_id", "report_messages", ["thread_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_report_messages_thread_id", table_name="report_messages")
    op.drop_index("ix_report_messages_message_type", table_name="report_messages")
    op.drop_index("ix_report_messages_deleted_at", table_name="report_messages")
    op.drop_table("report_messages")
