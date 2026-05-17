"""expand encrypted secret envelope storage

Revision ID: 0016_expand_encrypted_secret_ref
Revises: 0015_create_agent_steps
Create Date: 2026-05-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_expand_encrypted_secret_ref"
down_revision: str | None = "0015_create_agent_steps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "provider_credentials_metadata",
        "encrypted_secret_ref",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "provider_credentials_metadata",
        "encrypted_secret_ref",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
