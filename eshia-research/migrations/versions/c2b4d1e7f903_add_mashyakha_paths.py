"""add source-preserved Faqih Mashyakha paths

Revision ID: c2b4d1e7f903
Revises: fa7e9c2d4b51
Create Date: 2026-08-10 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c2b4d1e7f903"
down_revision: str | Sequence[str] | None = "fa7e9c2d4b51"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("mashyakha_paths"):
        return
    op.create_table(
        "mashyakha_paths",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_book_id", sa.String(length=64), nullable=False),
        sa.Column("source_key", sa.String(length=64), nullable=False),
        sa.Column("source_chapter", sa.Integer(), nullable=False),
        sa.Column("source_hadith_number", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("target_raw", sa.Text(), nullable=True),
        sa.Column("target_normalised", sa.String(length=512), nullable=True),
        sa.Column("source_text_ar", sa.Text(), nullable=False),
        sa.Column("source_text_en", sa.Text(), nullable=True),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("parsed_path_json", sa.JSON(), nullable=True),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key", "source_chapter", name="uq_mashyakha_path_source_chapter"),
    )
    op.create_index(op.f("ix_mashyakha_paths_source_book_id"), "mashyakha_paths", ["source_book_id"])
    op.create_index(op.f("ix_mashyakha_paths_source_key"), "mashyakha_paths", ["source_key"])
    op.create_index(op.f("ix_mashyakha_paths_target_normalised"), "mashyakha_paths", ["target_normalised"])
    op.create_index(op.f("ix_mashyakha_paths_source_sha256"), "mashyakha_paths", ["source_sha256"])
    op.create_index(op.f("ix_mashyakha_paths_review_status"), "mashyakha_paths", ["review_status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_mashyakha_paths_review_status"), table_name="mashyakha_paths")
    op.drop_index(op.f("ix_mashyakha_paths_source_sha256"), table_name="mashyakha_paths")
    op.drop_index(op.f("ix_mashyakha_paths_target_normalised"), table_name="mashyakha_paths")
    op.drop_index(op.f("ix_mashyakha_paths_source_key"), table_name="mashyakha_paths")
    op.drop_index(op.f("ix_mashyakha_paths_source_book_id"), table_name="mashyakha_paths")
    op.drop_table("mashyakha_paths")
