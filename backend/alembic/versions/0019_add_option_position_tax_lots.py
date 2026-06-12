"""add option position tax lots

Revision ID: 0019_option_position_tax_lots
Revises: 0018_account_detail_enrichment
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_option_position_tax_lots"
down_revision: str | None = "0018_account_detail_enrichment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("option_positions", sa.Column("tax_lots", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("option_positions", "tax_lots")
