"""add chains, chain_nodes and narrators tables

Revision ID: 9b4e5c7d1f20
Revises: 7c3a9a1a2b4f
Create Date: 2026-07-06 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "9b4e5c7d1f20"
down_revision: str | Sequence[str] | None = "7c3a9a1a2b4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "narrators",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("canonical_name_ar", sa.String(length=512), nullable=False),
        sa.Column("canonical_name_norm", sa.String(length=512), nullable=False),
        sa.Column("canonical_name_en", sa.String(length=512), nullable=True),
        sa.Column("kunya", sa.String(length=256), nullable=True),
        sa.Column("laqab", sa.String(length=256), nullable=True),
        sa.Column("nisba", sa.String(length=256), nullable=True),
        sa.Column("father_name", sa.String(length=256), nullable=True),
        sa.Column("death_year_note", sa.String(length=128), nullable=True),
        sa.Column("generation_layer", sa.Integer(), nullable=True),
        sa.Column("school_or_sect", sa.String(length=128), nullable=True),
        sa.Column("summary_status", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_narrators_canonical_name_norm"), "narrators", ["canonical_name_norm"], unique=False
    )

    op.create_table(
        "chains",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hadith_id", sa.Integer(), nullable=False),
        sa.Column("chain_number", sa.Integer(), nullable=False),
        sa.Column("raw_isnad", sa.Text(), nullable=False),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("node_count", sa.Integer(), nullable=False),
        sa.Column("flags", sa.String(length=512), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hadith_id", "chain_number", name="uq_chains_hadith_number"),
    )
    op.create_index(op.f("ix_chains_hadith_id"), "chains", ["hadith_id"], unique=False)
    op.create_index(op.f("ix_chains_review_status"), "chains", ["review_status"], unique=False)

    op.create_table(
        "chain_nodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("raw_token", sa.Text(), nullable=False),
        sa.Column("token_normalised", sa.String(length=512), nullable=False),
        sa.Column("transmission_phrase", sa.String(length=64), nullable=True),
        sa.Column("node_type", sa.String(length=32), nullable=False),
        sa.Column("relation_kind", sa.String(length=32), nullable=True),
        sa.Column("canonical_narrator_id", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("resolution_method", sa.String(length=64), nullable=True),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["chain_id"], ["chains.id"]),
        sa.ForeignKeyConstraint(["canonical_narrator_id"], ["narrators.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chain_id", "position", name="uq_chain_nodes_chain_position"),
    )
    op.create_index(op.f("ix_chain_nodes_chain_id"), "chain_nodes", ["chain_id"], unique=False)
    op.create_index(
        op.f("ix_chain_nodes_token_normalised"), "chain_nodes", ["token_normalised"], unique=False
    )
    op.create_index(op.f("ix_chain_nodes_node_type"), "chain_nodes", ["node_type"], unique=False)
    op.create_index(
        op.f("ix_chain_nodes_canonical_narrator_id"),
        "chain_nodes",
        ["canonical_narrator_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chain_nodes_canonical_narrator_id"), table_name="chain_nodes")
    op.drop_index(op.f("ix_chain_nodes_node_type"), table_name="chain_nodes")
    op.drop_index(op.f("ix_chain_nodes_token_normalised"), table_name="chain_nodes")
    op.drop_index(op.f("ix_chain_nodes_chain_id"), table_name="chain_nodes")
    op.drop_table("chain_nodes")
    op.drop_index(op.f("ix_chains_review_status"), table_name="chains")
    op.drop_index(op.f("ix_chains_hadith_id"), table_name="chains")
    op.drop_table("chains")
    op.drop_index(op.f("ix_narrators_canonical_name_norm"), table_name="narrators")
    op.drop_table("narrators")
