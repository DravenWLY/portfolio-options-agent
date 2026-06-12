"""add account detail enrichment fields

Revision ID: 0018_account_detail_enrichment
Revises: 0017_sync_membership
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018_account_detail_enrichment"
down_revision: str | None = "0017_sync_membership"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cash_balances", sa.Column("available_cash", sa.Numeric(18, 2), nullable=True))
    op.add_column("cash_balances", sa.Column("buying_power", sa.Numeric(18, 2), nullable=True))
    op.add_column(
        "cash_balances",
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
    )

    op.add_column("stock_positions", sa.Column("instrument_name", sa.String(length=160), nullable=True))
    op.add_column("stock_positions", sa.Column("average_price", sa.Numeric(18, 4), nullable=True))
    op.add_column("stock_positions", sa.Column("open_pnl", sa.Numeric(18, 2), nullable=True))
    op.add_column(
        "stock_positions",
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
    )
    op.add_column("stock_positions", sa.Column("tax_lots", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.add_column("option_positions", sa.Column("open_pnl", sa.Numeric(18, 2), nullable=True))
    op.add_column(
        "option_positions",
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("option_positions", "currency")
    op.drop_column("option_positions", "open_pnl")

    op.drop_column("stock_positions", "tax_lots")
    op.drop_column("stock_positions", "currency")
    op.drop_column("stock_positions", "open_pnl")
    op.drop_column("stock_positions", "average_price")
    op.drop_column("stock_positions", "instrument_name")

    op.drop_column("cash_balances", "currency")
    op.drop_column("cash_balances", "buying_power")
    op.drop_column("cash_balances", "available_cash")
