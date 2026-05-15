"""add cash balance provenance

Revision ID: 0004_add_cash_balance_provenance
Revises: 0003_create_cash_balances
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_cash_balance_provenance"
down_revision: str | None = "0003_create_cash_balances"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cash_balances",
        sa.Column("source", sa.String(length=40), server_default="manual", nullable=False),
    )
    op.add_column("cash_balances", sa.Column("source_ref", sa.String(length=120), nullable=True))
    op.add_column(
        "cash_balances",
        sa.Column("data_freshness_status", sa.String(length=40), server_default="unknown", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("cash_balances", "data_freshness_status")
    op.drop_column("cash_balances", "source_ref")
    op.drop_column("cash_balances", "source")
