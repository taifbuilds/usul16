"""add source-preserving hadith commentary passages

Revision ID: e4c91f7b2d68
Revises: a6c8d2e4f190
Create Date: 2026-07-28 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e4c91f7b2d68"
down_revision: str | Sequence[str] | None = "a6c8d2e4f190"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hadith_commentaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("commentary_book_id", sa.Integer(), nullable=False),
        sa.Column("hadith_id", sa.Integer(), nullable=True),
        sa.Column("source_key", sa.String(length=64), nullable=False),
        sa.Column("source_sequence", sa.Integer(), nullable=False),
        sa.Column("source_label", sa.String(length=256), nullable=True),
        sa.Column("section_title", sa.String(length=1024), nullable=True),
        sa.Column("report_raw", sa.Text(), nullable=True),
        sa.Column("report_normalised", sa.Text(), nullable=True),
        sa.Column("commentary_raw", sa.Text(), nullable=False),
        sa.Column("commentary_normalised", sa.Text(), nullable=False),
        sa.Column("volume_start", sa.Integer(), nullable=False),
        sa.Column("volume_end", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("match_status", sa.String(length=32), nullable=False),
        sa.Column("match_method", sa.String(length=64), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("matcher_version", sa.String(length=64), nullable=False),
        sa.Column("match_evidence_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["commentary_book_id"], ["books.id"]),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "commentary_book_id", "source_key", "source_sequence",
            name="uq_hadith_commentaries_source_sequence",
        ),
        sa.UniqueConstraint(
            "source_key", "hadith_id", name="uq_hadith_commentaries_source_hadith",
        ),
    )
    op.create_index(
        op.f("ix_hadith_commentaries_commentary_book_id"),
        "hadith_commentaries",
        ["commentary_book_id"],
    )
    op.create_index(
        op.f("ix_hadith_commentaries_hadith_id"), "hadith_commentaries", ["hadith_id"]
    )
    op.create_index(
        op.f("ix_hadith_commentaries_source_key"), "hadith_commentaries", ["source_key"]
    )
    op.create_index(
        op.f("ix_hadith_commentaries_volume_start"), "hadith_commentaries", ["volume_start"]
    )
    op.create_index(
        op.f("ix_hadith_commentaries_match_status"), "hadith_commentaries", ["match_status"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_hadith_commentaries_match_status"), table_name="hadith_commentaries")
    op.drop_index(op.f("ix_hadith_commentaries_volume_start"), table_name="hadith_commentaries")
    op.drop_index(op.f("ix_hadith_commentaries_source_key"), table_name="hadith_commentaries")
    op.drop_index(op.f("ix_hadith_commentaries_hadith_id"), table_name="hadith_commentaries")
    op.drop_index(op.f("ix_hadith_commentaries_commentary_book_id"), table_name="hadith_commentaries")
    op.drop_table("hadith_commentaries")
