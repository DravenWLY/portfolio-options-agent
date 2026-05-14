"""create cash balances table

Revision ID: 0003_create_cash_balances
Revises: 0002_create_accounts
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_create_cash_balances"
down_revision: str | None = "0002_create_accounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cash_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_cash", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("reserved_collateral_cash", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("free_cash", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("premium_income_cash", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("dca_cash", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cash_balances_account_id", "cash_balances", ["account_id"], unique=False)
    op.create_index("ix_cash_balances_account_id_as_of", "cash_balances", ["account_id", "as_of"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cash_balances_account_id_as_of", table_name="cash_balances")
    op.drop_index("ix_cash_balances_account_id", table_name="cash_balances")
    op.drop_table("cash_balances")
