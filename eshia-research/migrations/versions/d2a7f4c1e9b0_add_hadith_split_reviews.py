"""add hadith split reviews

Revision ID: d2a7f4c1e9b0
Revises: c7d81f42ab35
Create Date: 2026-07-07 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d2a7f4c1e9b0"
down_revision: str | Sequence[str] | None = "c7d81f42ab35"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hadith_split_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hadith_id", sa.Integer(), nullable=False),
        sa.Column("approved_isnad_raw", sa.Text(), nullable=True),
        sa.Column("approved_matn_raw", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("reviewer", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("split_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hadith_id", name="uq_hadith_split_reviews_hadith"),
    )
    op.create_index(
        op.f("ix_hadith_split_reviews_hadith_id"),
        "hadith_split_reviews",
        ["hadith_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hadith_split_reviews_review_status"),
        "hadith_split_reviews",
        ["review_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_hadith_split_reviews_review_status"), table_name="hadith_split_reviews")
    op.drop_index(op.f("ix_hadith_split_reviews_hadith_id"), table_name="hadith_split_reviews")
    op.drop_table("hadith_split_reviews")
