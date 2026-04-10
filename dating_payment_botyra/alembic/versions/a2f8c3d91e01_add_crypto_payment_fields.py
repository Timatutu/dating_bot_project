"""add crypto payment fields (deposit_address, expires_at)

Revision ID: a2f8c3d91e01
Revises: 1bcc2f5fb4dd
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2f8c3d91e01"
down_revision: Union[str, Sequence[str], None] = "1bcc2f5fb4dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("deposit_address", sa.String(64), nullable=True))
    op.add_column("payments", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("payments", "expires_at")
    op.drop_column("payments", "deposit_address")
