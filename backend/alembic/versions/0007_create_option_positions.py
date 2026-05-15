"""create option positions table

Revision ID: 0007_create_option_positions
Revises: 0006_create_option_contracts
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_create_option_positions"
down_revision: str | None = "0006_create_option_contracts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "option_positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("option_contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_side", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("average_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("market_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("market_value", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
        sa.Column("source", sa.String(length=40), server_default="manual", nullable=False),
        sa.Column("source_ref", sa.String(length=120), nullable=True),
        sa.Column("data_freshness_status", sa.String(length=40), server_default="unknown", nullable=False),
        sa.Column("raw_provider_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["option_contract_id"], ["option_contracts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_option_positions_account_id", "option_positions", ["account_id"], unique=False)
    op.create_index(
        "ix_option_positions_account_status",
        "option_positions",
        ["account_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_option_positions_contract_id",
        "option_positions",
        ["option_contract_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_option_positions_contract_id", table_name="option_positions")
    op.drop_index("ix_option_positions_account_status", table_name="option_positions")
    op.drop_index("ix_option_positions_account_id", table_name="option_positions")
    op.drop_table("option_positions")
