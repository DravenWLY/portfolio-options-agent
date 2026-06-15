"""add saved artifact snapshot to report threads

Revision ID: 0020_saved_review_artifacts
Revises: 0019_option_position_tax_lots
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020_saved_review_artifacts"
down_revision: str | None = "0019_option_position_tax_lots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("report_threads", sa.Column("saved_artifact_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_table(
        "saved_review_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_kind", sa.String(length=40), nullable=False),
        sa.Column("source_reference", sa.String(length=90), nullable=False),
        sa.Column("scope_metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("deterministic_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("agent_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "review_pipeline_label",
            sa.String(length=120),
            server_default="Portfolio Copilot review pipeline",
            nullable=False,
        ),
        sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("caveat_codes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source_kind", "source_reference", name="uq_saved_review_sources_user_source"),
    )
    op.create_index("ix_saved_review_sources_deleted_at", "saved_review_sources", ["deleted_at"], unique=False)
    op.create_index(
        "ix_saved_review_sources_source_reference",
        "saved_review_sources",
        ["source_reference"],
        unique=False,
    )
    op.create_index(
        "ix_saved_review_sources_user_created_at",
        "saved_review_sources",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_saved_review_sources_user_created_at", table_name="saved_review_sources")
    op.drop_index("ix_saved_review_sources_source_reference", table_name="saved_review_sources")
    op.drop_index("ix_saved_review_sources_deleted_at", table_name="saved_review_sources")
    op.drop_table("saved_review_sources")
    op.drop_column("report_threads", "saved_artifact_json")
