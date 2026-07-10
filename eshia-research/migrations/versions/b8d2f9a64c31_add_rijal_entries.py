"""add rijal entries, statements, aliases and occurrences

Revision ID: b8d2f9a64c31
Revises: 9b4e5c7d1f20
Create Date: 2026-07-06 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b8d2f9a64c31"
down_revision: str | Sequence[str] | None = "9b4e5c7d1f20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rijal_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("narrator_id", sa.Integer(), nullable=True),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("page_start_id", sa.Integer(), nullable=True),
        sa.Column("page_end_id", sa.Integer(), nullable=True),
        sa.Column("entry_kind", sa.String(length=64), nullable=False),
        sa.Column("entry_number", sa.Integer(), nullable=True),
        sa.Column("title_raw", sa.String(length=512), nullable=False),
        sa.Column("title_normalised", sa.String(length=512), nullable=False),
        sa.Column("canonical_name_raw", sa.String(length=512), nullable=False),
        sa.Column("canonical_name_normalised", sa.String(length=512), nullable=False),
        sa.Column("volume_start", sa.Integer(), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("volume_end", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("text_raw", sa.Text(), nullable=False),
        sa.Column("text_normalised", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("flags", sa.String(length=512), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.ForeignKeyConstraint(["narrator_id"], ["narrators.id"]),
        sa.ForeignKeyConstraint(["page_end_id"], ["pages.id"]),
        sa.ForeignKeyConstraint(["page_start_id"], ["pages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "entry_kind", "entry_number", name="uq_rijal_entry_number"),
    )
    op.create_index(op.f("ix_rijal_entries_book_id"), "rijal_entries", ["book_id"], unique=False)
    op.create_index(
        op.f("ix_rijal_entries_canonical_name_normalised"),
        "rijal_entries",
        ["canonical_name_normalised"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rijal_entries_entry_number"), "rijal_entries", ["entry_number"], unique=False
    )
    op.create_index(
        op.f("ix_rijal_entries_narrator_id"), "rijal_entries", ["narrator_id"], unique=False
    )
    op.create_index(
        op.f("ix_rijal_entries_review_status"), "rijal_entries", ["review_status"], unique=False
    )
    op.create_index(
        op.f("ix_rijal_entries_title_normalised"), "rijal_entries", ["title_normalised"], unique=False
    )

    op.create_table(
        "narrator_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("narrator_id", sa.Integer(), nullable=False),
        sa.Column("source_entry_id", sa.Integer(), nullable=True),
        sa.Column("alias_raw", sa.String(length=512), nullable=False),
        sa.Column("alias_normalised", sa.String(length=512), nullable=False),
        sa.Column("alias_type", sa.String(length=32), nullable=False),
        sa.Column("source_note", sa.String(length=256), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["narrator_id"], ["narrators.id"]),
        sa.ForeignKeyConstraint(["source_entry_id"], ["rijal_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "narrator_id",
            "alias_normalised",
            "alias_type",
            "source_entry_id",
            name="uq_narrator_alias_source",
        ),
    )
    op.create_index(
        op.f("ix_narrator_aliases_alias_normalised"),
        "narrator_aliases",
        ["alias_normalised"],
        unique=False,
    )
    op.create_index(
        op.f("ix_narrator_aliases_narrator_id"), "narrator_aliases", ["narrator_id"], unique=False
    )
    op.create_index(
        op.f("ix_narrator_aliases_source_entry_id"),
        "narrator_aliases",
        ["source_entry_id"],
        unique=False,
    )

    op.create_table(
        "rijal_occurrences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("narrator_id", sa.Integer(), nullable=True),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("related_name_raw", sa.String(length=512), nullable=False),
        sa.Column("related_name_normalised", sa.String(length=512), nullable=False),
        sa.Column("source_ref_raw", sa.Text(), nullable=True),
        sa.Column("evidence_text_raw", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["entry_id"], ["rijal_entries.id"]),
        sa.ForeignKeyConstraint(["narrator_id"], ["narrators.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rijal_occurrences_direction"), "rijal_occurrences", ["direction"], unique=False
    )
    op.create_index(
        op.f("ix_rijal_occurrences_entry_id"), "rijal_occurrences", ["entry_id"], unique=False
    )
    op.create_index(
        op.f("ix_rijal_occurrences_narrator_id"),
        "rijal_occurrences",
        ["narrator_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rijal_occurrences_related_name_normalised"),
        "rijal_occurrences",
        ["related_name_normalised"],
        unique=False,
    )

    op.create_table(
        "rijal_statements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("narrator_id", sa.Integer(), nullable=True),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("statement_type", sa.String(length=64), nullable=False),
        sa.Column("quote_raw", sa.Text(), nullable=False),
        sa.Column("quote_normalised", sa.Text(), nullable=False),
        sa.Column("evidence_text_raw", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["entry_id"], ["rijal_entries.id"]),
        sa.ForeignKeyConstraint(["narrator_id"], ["narrators.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rijal_statements_entry_id"), "rijal_statements", ["entry_id"], unique=False
    )
    op.create_index(
        op.f("ix_rijal_statements_narrator_id"), "rijal_statements", ["narrator_id"], unique=False
    )
    op.create_index(
        op.f("ix_rijal_statements_source_name"), "rijal_statements", ["source_name"], unique=False
    )
    op.create_index(
        op.f("ix_rijal_statements_statement_type"),
        "rijal_statements",
        ["statement_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_rijal_statements_statement_type"), table_name="rijal_statements")
    op.drop_index(op.f("ix_rijal_statements_source_name"), table_name="rijal_statements")
    op.drop_index(op.f("ix_rijal_statements_narrator_id"), table_name="rijal_statements")
    op.drop_index(op.f("ix_rijal_statements_entry_id"), table_name="rijal_statements")
    op.drop_table("rijal_statements")

    op.drop_index(
        op.f("ix_rijal_occurrences_related_name_normalised"), table_name="rijal_occurrences"
    )
    op.drop_index(op.f("ix_rijal_occurrences_narrator_id"), table_name="rijal_occurrences")
    op.drop_index(op.f("ix_rijal_occurrences_entry_id"), table_name="rijal_occurrences")
    op.drop_index(op.f("ix_rijal_occurrences_direction"), table_name="rijal_occurrences")
    op.drop_table("rijal_occurrences")

    op.drop_index(op.f("ix_narrator_aliases_source_entry_id"), table_name="narrator_aliases")
    op.drop_index(op.f("ix_narrator_aliases_narrator_id"), table_name="narrator_aliases")
    op.drop_index(op.f("ix_narrator_aliases_alias_normalised"), table_name="narrator_aliases")
    op.drop_table("narrator_aliases")

    op.drop_index(op.f("ix_rijal_entries_title_normalised"), table_name="rijal_entries")
    op.drop_index(op.f("ix_rijal_entries_review_status"), table_name="rijal_entries")
    op.drop_index(op.f("ix_rijal_entries_narrator_id"), table_name="rijal_entries")
    op.drop_index(op.f("ix_rijal_entries_entry_number"), table_name="rijal_entries")
    op.drop_index(op.f("ix_rijal_entries_canonical_name_normalised"), table_name="rijal_entries")
    op.drop_index(op.f("ix_rijal_entries_book_id"), table_name="rijal_entries")
    op.drop_table("rijal_entries")
