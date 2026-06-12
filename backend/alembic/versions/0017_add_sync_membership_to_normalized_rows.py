"""add sync membership to normalized account rows

Revision ID: 0017_sync_membership
Revises: 0016_expand_encrypted_secret_ref
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017_sync_membership"
down_revision: str | None = "0016_expand_encrypted_secret_ref"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in ("cash_balances", "stock_positions", "option_positions"):
        op.add_column(table_name, sa.Column("sync_run_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f"fk_{table_name}_sync_run_id_broker_sync_runs",
            table_name,
            "broker_sync_runs",
            ["sync_run_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(f"ix_{table_name}_sync_run_id", table_name, ["sync_run_id"], unique=False)


def downgrade() -> None:
    for table_name in ("option_positions", "stock_positions", "cash_balances"):
        op.drop_index(f"ix_{table_name}_sync_run_id", table_name=table_name)
        op.drop_constraint(f"fk_{table_name}_sync_run_id_broker_sync_runs", table_name, type_="foreignkey")
        op.drop_column(table_name, "sync_run_id")
