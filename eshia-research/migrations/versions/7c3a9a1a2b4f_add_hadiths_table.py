"""add hadiths table

Revision ID: 7c3a9a1a2b4f
Revises: 20ebd2b65836
Create Date: 2026-07-06 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "7c3a9a1a2b4f"
down_revision: str | Sequence[str] | None = "20ebd2b65836"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hadiths",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=128), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("page_start_id", sa.Integer(), nullable=True),
        sa.Column("page_end_id", sa.Integer(), nullable=True),
        sa.Column("sequence_in_book", sa.Integer(), nullable=False),
        sa.Column("sequence_in_page", sa.Integer(), nullable=False),
        sa.Column("printed_number", sa.String(length=128), nullable=True),
        sa.Column("volume_start", sa.Integer(), nullable=True),
        sa.Column("volume_end", sa.Integer(), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("section_title", sa.String(length=1024), nullable=True),
        sa.Column("full_text_raw", sa.Text(), nullable=False),
        sa.Column("full_text_normalised", sa.Text(), nullable=False),
        sa.Column("isnad_raw", sa.Text(), nullable=True),
        sa.Column("isnad_normalised", sa.Text(), nullable=True),
        sa.Column("matn_raw", sa.Text(), nullable=False),
        sa.Column("matn_normalised", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("extraction_method", sa.String(length=64), nullable=False),
        sa.Column("extraction_confidence", sa.Integer(), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.ForeignKeyConstraint(["page_end_id"], ["pages.id"]),
        sa.ForeignKeyConstraint(["page_start_id"], ["pages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "sequence_in_book", name="uq_hadiths_book_sequence"),
        sa.UniqueConstraint("public_id", name="uq_hadiths_public_id"),
    )
    op.create_index(op.f("ix_hadiths_book_id"), "hadiths", ["book_id"], unique=False)
    op.create_index(op.f("ix_hadiths_public_id"), "hadiths", ["public_id"], unique=False)
    op.create_index(op.f("ix_hadiths_review_status"), "hadiths", ["review_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_hadiths_review_status"), table_name="hadiths")
    op.drop_index(op.f("ix_hadiths_public_id"), table_name="hadiths")
    op.drop_index(op.f("ix_hadiths_book_id"), table_name="hadiths")
    op.drop_table("hadiths")
