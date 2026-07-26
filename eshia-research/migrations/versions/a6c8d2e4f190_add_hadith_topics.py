"""add hadith topics and assignments

Revision ID: a6c8d2e4f190
Revises: f1a4b8e6c210
Create Date: 2026-07-23 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a6c8d2e4f190"
down_revision: str | Sequence[str] | None = "f1a4b8e6c210"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("hashtag", sa.String(length=96), nullable=False),
        sa.Column("name_en", sa.String(length=512), nullable=False),
        sa.Column("name_ar", sa.String(length=512), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_key", sa.String(length=160), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("aliases_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_topics_slug"),
        sa.UniqueConstraint("source", "source_key", name="uq_topics_source_key"),
    )
    op.create_index(op.f("ix_topics_slug"), "topics", ["slug"])
    op.create_index(op.f("ix_topics_hashtag"), "topics", ["hashtag"])
    op.create_index(op.f("ix_topics_kind"), "topics", ["kind"])
    op.create_index(op.f("ix_topics_source"), "topics", ["source"])

    op.create_table(
        "hadith_topic_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hadith_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("relevance", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("assignment_method", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "hadith_id", "topic_id", name="uq_hadith_topic_assignment"
        ),
    )
    op.create_index(
        op.f("ix_hadith_topic_assignments_hadith_id"),
        "hadith_topic_assignments",
        ["hadith_id"],
    )
    op.create_index(
        op.f("ix_hadith_topic_assignments_topic_id"),
        "hadith_topic_assignments",
        ["topic_id"],
    )
    op.create_index(
        op.f("ix_hadith_topic_assignments_assignment_method"),
        "hadith_topic_assignments",
        ["assignment_method"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_hadith_topic_assignments_assignment_method"),
        table_name="hadith_topic_assignments",
    )
    op.drop_index(
        op.f("ix_hadith_topic_assignments_topic_id"),
        table_name="hadith_topic_assignments",
    )
    op.drop_index(
        op.f("ix_hadith_topic_assignments_hadith_id"),
        table_name="hadith_topic_assignments",
    )
    op.drop_table("hadith_topic_assignments")
    op.drop_index(op.f("ix_topics_source"), table_name="topics")
    op.drop_index(op.f("ix_topics_kind"), table_name="topics")
    op.drop_index(op.f("ix_topics_hashtag"), table_name="topics")
    op.drop_index(op.f("ix_topics_slug"), table_name="topics")
    op.drop_table("topics")
