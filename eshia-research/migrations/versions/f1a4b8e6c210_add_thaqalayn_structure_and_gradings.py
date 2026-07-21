"""add thaqalayn structure maps and hadith gradings

Revision ID: f1a4b8e6c210
Revises: e8f2c5d9a341
Create Date: 2026-07-21 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f1a4b8e6c210"
down_revision: str | Sequence[str] | None = "e8f2c5d9a341"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "thaqalayn_structure_maps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hadith_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("remote_book_id", sa.String(length=128), nullable=True),
        sa.Column("remote_id", sa.Integer(), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("kitab_id", sa.String(length=32), nullable=False),
        sa.Column("kitab_name_en", sa.String(length=512), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("chapter_name_en", sa.String(length=512), nullable=False),
        sa.Column("number_in_chapter", sa.Integer(), nullable=True),
        sa.Column("number_prefix_en", sa.Integer(), nullable=True),
        sa.Column("position_computed", sa.Integer(), nullable=True),
        sa.Column("numbering_flags", sa.JSON(), nullable=True),
        sa.Column("thaqalayn_url", sa.String(length=1024), nullable=True),
        sa.Column("mapping_status", sa.String(length=32), nullable=False),
        sa.Column("match_method", sa.String(length=32), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("matcher_version", sa.String(length=32), nullable=False),
        sa.Column("remote_arabic_sha256", sa.String(length=64), nullable=True),
        sa.Column("raw_ref_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hadith_id", "source", name="uq_structure_map_hadith_source"),
        sa.UniqueConstraint(
            "source", "remote_book_id", "remote_id", name="uq_structure_map_remote_row"
        ),
    )
    op.create_index(
        op.f("ix_thaqalayn_structure_maps_hadith_id"),
        "thaqalayn_structure_maps",
        ["hadith_id"],
    )
    op.create_index(
        op.f("ix_thaqalayn_structure_maps_source"), "thaqalayn_structure_maps", ["source"]
    )
    op.create_index(
        op.f("ix_thaqalayn_structure_maps_volume"), "thaqalayn_structure_maps", ["volume"]
    )
    op.create_index(
        op.f("ix_thaqalayn_structure_maps_kitab_id"), "thaqalayn_structure_maps", ["kitab_id"]
    )
    op.create_index(
        op.f("ix_thaqalayn_structure_maps_chapter_id"),
        "thaqalayn_structure_maps",
        ["chapter_id"],
    )
    op.create_index(
        op.f("ix_thaqalayn_structure_maps_mapping_status"),
        "thaqalayn_structure_maps",
        ["mapping_status"],
    )
    op.create_index(
        op.f("ix_thaqalayn_structure_maps_match_method"),
        "thaqalayn_structure_maps",
        ["match_method"],
    )

    op.create_table(
        "hadith_gradings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hadith_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("grader_key", sa.String(length=64), nullable=False),
        sa.Column("author_name_en", sa.String(length=256), nullable=False),
        sa.Column("grade_ar", sa.String(length=256), nullable=False),
        sa.Column("grade_en", sa.String(length=256), nullable=True),
        sa.Column("reference_en", sa.String(length=512), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "hadith_id", "source", "display_order", name="uq_hadith_grading_order"
        ),
    )
    op.create_index(op.f("ix_hadith_gradings_hadith_id"), "hadith_gradings", ["hadith_id"])
    op.create_index(op.f("ix_hadith_gradings_source"), "hadith_gradings", ["source"])
    op.create_index(op.f("ix_hadith_gradings_grader_key"), "hadith_gradings", ["grader_key"])


def downgrade() -> None:
    op.drop_index(op.f("ix_hadith_gradings_grader_key"), table_name="hadith_gradings")
    op.drop_index(op.f("ix_hadith_gradings_source"), table_name="hadith_gradings")
    op.drop_index(op.f("ix_hadith_gradings_hadith_id"), table_name="hadith_gradings")
    op.drop_table("hadith_gradings")

    op.drop_index(
        op.f("ix_thaqalayn_structure_maps_match_method"), table_name="thaqalayn_structure_maps"
    )
    op.drop_index(
        op.f("ix_thaqalayn_structure_maps_mapping_status"),
        table_name="thaqalayn_structure_maps",
    )
    op.drop_index(
        op.f("ix_thaqalayn_structure_maps_chapter_id"), table_name="thaqalayn_structure_maps"
    )
    op.drop_index(
        op.f("ix_thaqalayn_structure_maps_kitab_id"), table_name="thaqalayn_structure_maps"
    )
    op.drop_index(
        op.f("ix_thaqalayn_structure_maps_volume"), table_name="thaqalayn_structure_maps"
    )
    op.drop_index(
        op.f("ix_thaqalayn_structure_maps_source"), table_name="thaqalayn_structure_maps"
    )
    op.drop_index(
        op.f("ix_thaqalayn_structure_maps_hadith_id"), table_name="thaqalayn_structure_maps"
    )
    op.drop_table("thaqalayn_structure_maps")
