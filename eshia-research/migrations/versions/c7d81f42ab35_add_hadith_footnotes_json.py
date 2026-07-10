"""add hadiths.footnotes_json

Revision ID: c7d81f42ab35
Revises: c41f3e4d9a21
Create Date: 2026-07-06 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c7d81f42ab35"
down_revision: str | Sequence[str] | None = "c41f3e4d9a21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("hadiths", sa.Column("footnotes_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("hadiths", "footnotes_json")
