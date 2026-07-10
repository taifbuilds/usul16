"""add chain node resolution candidates

Revision ID: c41f3e4d9a21
Revises: b8d2f9a64c31
Create Date: 2026-07-06 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c41f3e4d9a21"
down_revision: str | Sequence[str] | None = "b8d2f9a64c31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chain_node_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chain_node_id", sa.Integer(), nullable=False),
        sa.Column("narrator_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("match_type", sa.String(length=64), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("resolver_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chain_node_id"], ["chain_nodes.id"]),
        sa.ForeignKeyConstraint(["narrator_id"], ["narrators.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chain_node_id",
            "narrator_id",
            "resolver_version",
            name="uq_chain_node_candidate_version",
        ),
    )
    op.create_index(
        op.f("ix_chain_node_candidates_chain_node_id"),
        "chain_node_candidates",
        ["chain_node_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chain_node_candidates_match_type"),
        "chain_node_candidates",
        ["match_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chain_node_candidates_narrator_id"),
        "chain_node_candidates",
        ["narrator_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chain_node_candidates_resolver_version"),
        "chain_node_candidates",
        ["resolver_version"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chain_node_candidates_score"),
        "chain_node_candidates",
        ["score"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chain_node_candidates_score"), table_name="chain_node_candidates")
    op.drop_index(
        op.f("ix_chain_node_candidates_resolver_version"), table_name="chain_node_candidates"
    )
    op.drop_index(op.f("ix_chain_node_candidates_narrator_id"), table_name="chain_node_candidates")
    op.drop_index(op.f("ix_chain_node_candidates_match_type"), table_name="chain_node_candidates")
    op.drop_index(op.f("ix_chain_node_candidates_chain_node_id"), table_name="chain_node_candidates")
    op.drop_table("chain_node_candidates")
