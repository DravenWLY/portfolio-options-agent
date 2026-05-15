"""create stock positions table

Revision ID: 0005_create_stock_positions
Revises: 0004_add_cash_balance_provenance
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_create_stock_positions"
down_revision: str | None = "0004_add_cash_balance_provenance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stock_positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(length=24), nullable=False),
        sa.Column("asset_type", sa.String(length=40), server_default="stock", nullable=False),
        sa.Column("quantity", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("cost_basis", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("market_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("market_value", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("source", sa.String(length=40), server_default="manual", nullable=False),
        sa.Column("source_ref", sa.String(length=120), nullable=True),
        sa.Column("data_freshness_status", sa.String(length=40), server_default="unknown", nullable=False),
        sa.Column("raw_provider_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_positions_account_id", "stock_positions", ["account_id"], unique=False)
    op.create_index(
        "ix_stock_positions_account_id_symbol",
        "stock_positions",
        ["account_id", "symbol"],
        unique=False,
    )
    op.create_index(
        "ix_stock_positions_account_id_as_of",
        "stock_positions",
        ["account_id", "as_of"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_stock_positions_account_id_as_of", table_name="stock_positions")
    op.drop_index("ix_stock_positions_account_id_symbol", table_name="stock_positions")
    op.drop_index("ix_stock_positions_account_id", table_name="stock_positions")
    op.drop_table("stock_positions")
