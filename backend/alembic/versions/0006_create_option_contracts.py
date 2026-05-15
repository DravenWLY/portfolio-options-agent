"""create option contracts table

Revision ID: 0006_create_option_contracts
Revises: 0005_create_stock_positions
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_create_option_contracts"
down_revision: str | None = "0005_create_stock_positions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "option_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occ_symbol", sa.String(length=64), nullable=False),
        sa.Column("underlying_symbol", sa.String(length=24), nullable=False),
        sa.Column("expiration_date", sa.Date(), nullable=False),
        sa.Column("strike", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("option_type", sa.String(length=4), nullable=False),
        sa.Column("style", sa.String(length=20), server_default="american", nullable=False),
        sa.Column("multiplier", sa.Numeric(precision=10, scale=2), server_default="100", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("occ_symbol", name="uq_option_contracts_occ_symbol"),
    )
    op.create_index(
        "ix_option_contracts_underlying_expiration",
        "option_contracts",
        ["underlying_symbol", "expiration_date"],
        unique=False,
    )
    op.create_index(
        "ix_option_contracts_lookup",
        "option_contracts",
        ["underlying_symbol", "expiration_date", "strike", "option_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_option_contracts_lookup", table_name="option_contracts")
    op.drop_index("ix_option_contracts_underlying_expiration", table_name="option_contracts")
    op.drop_table("option_contracts")
