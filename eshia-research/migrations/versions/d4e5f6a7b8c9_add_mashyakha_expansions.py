"""add reviewable Faqih Mashyakha expansion proposals

Revision ID: d4e5f6a7b8c9
Revises: c2b4d1e7f903
Create Date: 2026-08-10 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c2b4d1e7f903"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("mashyakha_expansions"):
        return
    op.create_table(
        "mashyakha_expansions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("mashyakha_path_id", sa.Integer(), nullable=False),
        sa.Column("match_method", sa.String(length=64), nullable=False),
        sa.Column("match_evidence_json", sa.JSON(), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chain_id"], ["chains.id"]),
        sa.ForeignKeyConstraint(["mashyakha_path_id"], ["mashyakha_paths.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chain_id", "mashyakha_path_id", name="uq_mashyakha_expansion_chain_path"),
    )
    op.create_index(op.f("ix_mashyakha_expansions_chain_id"), "mashyakha_expansions", ["chain_id"])
    op.create_index(
        op.f("ix_mashyakha_expansions_mashyakha_path_id"),
        "mashyakha_expansions",
        ["mashyakha_path_id"],
    )
    op.create_index(
        op.f("ix_mashyakha_expansions_match_method"), "mashyakha_expansions", ["match_method"]
    )
    op.create_index(
        op.f("ix_mashyakha_expansions_review_status"), "mashyakha_expansions", ["review_status"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_mashyakha_expansions_review_status"), table_name="mashyakha_expansions")
    op.drop_index(op.f("ix_mashyakha_expansions_match_method"), table_name="mashyakha_expansions")
    op.drop_index(
        op.f("ix_mashyakha_expansions_mashyakha_path_id"), table_name="mashyakha_expansions"
    )
    op.drop_index(op.f("ix_mashyakha_expansions_chain_id"), table_name="mashyakha_expansions")
    op.drop_table("mashyakha_expansions")
