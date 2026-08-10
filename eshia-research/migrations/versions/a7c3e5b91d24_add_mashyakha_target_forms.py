"""record every narrator form a Mashyakha entry vouches for

One entry can cover several narrators sharing a path ("عن محمد بن حمران؛ و جميل
بن دراج") and can name a two-step opening ("عن زرعة، عن سماعة"), so a single
``target_normalised`` cannot represent it.

Revision ID: a7c3e5b91d24
Revises: d4e5f6a7b8c9
Create Date: 2026-08-10 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a7c3e5b91d24"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("mashyakha_paths"):
        return True
    return any(column["name"] == name for column in inspector.get_columns("mashyakha_paths"))


def upgrade() -> None:
    if _has_column("target_forms_json"):
        return
    op.add_column("mashyakha_paths", sa.Column("target_forms_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    if not _has_column("target_forms_json"):
        return
    op.drop_column("mashyakha_paths", "target_forms_json")
