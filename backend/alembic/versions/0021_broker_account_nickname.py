"""add user-owned broker account nickname

Revision ID: 0021_broker_acct_nickname
Revises: 0020_saved_review_artifacts
Create Date: 2026-06-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021_broker_acct_nickname"
down_revision: str | None = "0020_saved_review_artifacts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("broker_accounts", sa.Column("user_nickname", sa.String(length=60), nullable=True))


def downgrade() -> None:
    op.drop_column("broker_accounts", "user_nickname")
