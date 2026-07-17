"""add translation tables

Revision ID: e8f2c5d9a341
Revises: d2a7f4c1e9b0
Create Date: 2026-07-12 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e8f2c5d9a341"
down_revision: str | Sequence[str] | None = "d2a7f4c1e9b0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hadith_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hadith_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("translation_version", sa.String(length=32), nullable=False),
        sa.Column("source_full_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_isnad_sha256", sa.String(length=64), nullable=True),
        sa.Column("source_matn_sha256", sa.String(length=64), nullable=False),
        sa.Column("rendered_isnad_en", sa.Text(), nullable=True),
        sa.Column("matn_translation", sa.Text(), nullable=True),
        sa.Column("full_translation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("risk_flags", sa.JSON(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("glossary_version", sa.String(length=64), nullable=True),
        sa.Column("qa_version", sa.String(length=64), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_estimate_usd", sa.Float(), nullable=True),
        sa.Column("provenance_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "hadith_id",
            "language",
            "translation_version",
            name="uq_hadith_translation_version",
        ),
    )
    op.create_index(op.f("ix_hadith_translations_hadith_id"), "hadith_translations", ["hadith_id"])
    op.create_index(op.f("ix_hadith_translations_language"), "hadith_translations", ["language"])
    op.create_index(op.f("ix_hadith_translations_risk_level"), "hadith_translations", ["risk_level"])
    op.create_index(
        op.f("ix_hadith_translations_source_full_sha256"),
        "hadith_translations",
        ["source_full_sha256"],
    )
    op.create_index(
        op.f("ix_hadith_translations_source_isnad_sha256"),
        "hadith_translations",
        ["source_isnad_sha256"],
    )
    op.create_index(
        op.f("ix_hadith_translations_source_matn_sha256"),
        "hadith_translations",
        ["source_matn_sha256"],
    )
    op.create_index(op.f("ix_hadith_translations_status"), "hadith_translations", ["status"])
    op.create_index(
        op.f("ix_hadith_translations_translation_version"),
        "hadith_translations",
        ["translation_version"],
    )

    op.create_table(
        "translation_segments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hadith_id", sa.Integer(), nullable=False),
        sa.Column("translation_id", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("translation_version", sa.String(length=32), nullable=False),
        sa.Column("segment_kind", sa.String(length=32), nullable=False),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("translation_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("risk_flags", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.ForeignKeyConstraint(["translation_id"], ["hadith_translations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "hadith_id",
            "language",
            "translation_version",
            "segment_kind",
            "segment_index",
            "source_sha256",
            name="uq_translation_segment_source",
        ),
    )
    op.create_index(op.f("ix_translation_segments_hadith_id"), "translation_segments", ["hadith_id"])
    op.create_index(op.f("ix_translation_segments_language"), "translation_segments", ["language"])
    op.create_index(op.f("ix_translation_segments_risk_level"), "translation_segments", ["risk_level"])
    op.create_index(
        op.f("ix_translation_segments_segment_kind"),
        "translation_segments",
        ["segment_kind"],
    )
    op.create_index(
        op.f("ix_translation_segments_source_sha256"),
        "translation_segments",
        ["source_sha256"],
    )
    op.create_index(op.f("ix_translation_segments_status"), "translation_segments", ["status"])
    op.create_index(
        op.f("ix_translation_segments_translation_id"),
        "translation_segments",
        ["translation_id"],
    )
    op.create_index(
        op.f("ix_translation_segments_translation_version"),
        "translation_segments",
        ["translation_version"],
    )

    op.create_table(
        "translation_glossary",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("term_ar", sa.String(length=512), nullable=False),
        sa.Column("term_norm", sa.String(length=512), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("term_en", sa.String(length=512), nullable=False),
        sa.Column("term_type", sa.String(length=32), nullable=False),
        sa.Column("policy", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("term_norm", "language", "version", name="uq_translation_glossary_term"),
    )
    op.create_index(op.f("ix_translation_glossary_active"), "translation_glossary", ["active"])
    op.create_index(op.f("ix_translation_glossary_language"), "translation_glossary", ["language"])
    op.create_index(op.f("ix_translation_glossary_policy"), "translation_glossary", ["policy"])
    op.create_index(op.f("ix_translation_glossary_term_norm"), "translation_glossary", ["term_norm"])
    op.create_index(op.f("ix_translation_glossary_term_type"), "translation_glossary", ["term_type"])
    op.create_index(op.f("ix_translation_glossary_version"), "translation_glossary", ["version"])

    op.create_table(
        "translation_memory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("source_norm", sa.Text(), nullable=False),
        sa.Column("translation_text", sa.Text(), nullable=False),
        sa.Column("source_hadith_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewer", sa.String(length=128), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_hadith_id"], ["hadiths.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("language", "source_sha256", name="uq_translation_memory_source"),
    )
    op.create_index(op.f("ix_translation_memory_language"), "translation_memory", ["language"])
    op.create_index(op.f("ix_translation_memory_source_hadith_id"), "translation_memory", ["source_hadith_id"])
    op.create_index(op.f("ix_translation_memory_source_sha256"), "translation_memory", ["source_sha256"])
    op.create_index(op.f("ix_translation_memory_status"), "translation_memory", ["status"])

    op.create_table(
        "translation_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_key", sa.String(length=128), nullable=False),
        sa.Column("source_book_id", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("glossary_version", sa.String(length=64), nullable=True),
        sa.Column("scope_json", sa.JSON(), nullable=True),
        sa.Column("batch_policy_json", sa.JSON(), nullable=True),
        sa.Column("hadith_count", sa.Integer(), nullable=False),
        sa.Column("segment_count", sa.Integer(), nullable=False),
        sa.Column("input_chars", sa.Integer(), nullable=False),
        sa.Column("estimated_input_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_key", name="uq_translation_job_key"),
    )
    op.create_index(op.f("ix_translation_jobs_job_key"), "translation_jobs", ["job_key"])
    op.create_index(op.f("ix_translation_jobs_language"), "translation_jobs", ["language"])
    op.create_index(op.f("ix_translation_jobs_source_book_id"), "translation_jobs", ["source_book_id"])
    op.create_index(op.f("ix_translation_jobs_status"), "translation_jobs", ["status"])

    op.create_table(
        "translation_job_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("hadith_id", sa.Integer(), nullable=False),
        sa.Column("segment_id", sa.Integer(), nullable=True),
        sa.Column("item_index", sa.Integer(), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hadith_id"], ["hadiths.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["translation_jobs.id"]),
        sa.ForeignKeyConstraint(["segment_id"], ["translation_segments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "item_index", name="uq_translation_job_item_index"),
    )
    op.create_index(op.f("ix_translation_job_items_hadith_id"), "translation_job_items", ["hadith_id"])
    op.create_index(op.f("ix_translation_job_items_job_id"), "translation_job_items", ["job_id"])
    op.create_index(op.f("ix_translation_job_items_risk_level"), "translation_job_items", ["risk_level"])
    op.create_index(op.f("ix_translation_job_items_segment_id"), "translation_job_items", ["segment_id"])
    op.create_index(op.f("ix_translation_job_items_source_sha256"), "translation_job_items", ["source_sha256"])
    op.create_index(op.f("ix_translation_job_items_status"), "translation_job_items", ["status"])

    op.create_table(
        "translation_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("request_json", sa.JSON(), nullable=True),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_estimate_usd", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["translation_job_items.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["translation_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_translation_attempts_item_id"), "translation_attempts", ["item_id"])
    op.create_index(op.f("ix_translation_attempts_job_id"), "translation_attempts", ["job_id"])
    op.create_index(op.f("ix_translation_attempts_status"), "translation_attempts", ["status"])

    op.create_table(
        "translation_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("translation_id", sa.Integer(), nullable=False),
        sa.Column("segment_id", sa.Integer(), nullable=True),
        sa.Column("reviewer", sa.String(length=128), nullable=False),
        sa.Column("decision_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("qa_flags_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["segment_id"], ["translation_segments.id"]),
        sa.ForeignKeyConstraint(["translation_id"], ["hadith_translations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_translation_reviews_decision_type"), "translation_reviews", ["decision_type"])
    op.create_index(op.f("ix_translation_reviews_reviewer"), "translation_reviews", ["reviewer"])
    op.create_index(op.f("ix_translation_reviews_segment_id"), "translation_reviews", ["segment_id"])
    op.create_index(op.f("ix_translation_reviews_severity"), "translation_reviews", ["severity"])
    op.create_index(op.f("ix_translation_reviews_translation_id"), "translation_reviews", ["translation_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_translation_reviews_translation_id"), table_name="translation_reviews")
    op.drop_index(op.f("ix_translation_reviews_severity"), table_name="translation_reviews")
    op.drop_index(op.f("ix_translation_reviews_segment_id"), table_name="translation_reviews")
    op.drop_index(op.f("ix_translation_reviews_reviewer"), table_name="translation_reviews")
    op.drop_index(op.f("ix_translation_reviews_decision_type"), table_name="translation_reviews")
    op.drop_table("translation_reviews")

    op.drop_index(op.f("ix_translation_attempts_status"), table_name="translation_attempts")
    op.drop_index(op.f("ix_translation_attempts_job_id"), table_name="translation_attempts")
    op.drop_index(op.f("ix_translation_attempts_item_id"), table_name="translation_attempts")
    op.drop_table("translation_attempts")

    op.drop_index(op.f("ix_translation_job_items_status"), table_name="translation_job_items")
    op.drop_index(op.f("ix_translation_job_items_source_sha256"), table_name="translation_job_items")
    op.drop_index(op.f("ix_translation_job_items_segment_id"), table_name="translation_job_items")
    op.drop_index(op.f("ix_translation_job_items_risk_level"), table_name="translation_job_items")
    op.drop_index(op.f("ix_translation_job_items_job_id"), table_name="translation_job_items")
    op.drop_index(op.f("ix_translation_job_items_hadith_id"), table_name="translation_job_items")
    op.drop_table("translation_job_items")

    op.drop_index(op.f("ix_translation_jobs_status"), table_name="translation_jobs")
    op.drop_index(op.f("ix_translation_jobs_source_book_id"), table_name="translation_jobs")
    op.drop_index(op.f("ix_translation_jobs_language"), table_name="translation_jobs")
    op.drop_index(op.f("ix_translation_jobs_job_key"), table_name="translation_jobs")
    op.drop_table("translation_jobs")

    op.drop_index(op.f("ix_translation_memory_status"), table_name="translation_memory")
    op.drop_index(op.f("ix_translation_memory_source_sha256"), table_name="translation_memory")
    op.drop_index(op.f("ix_translation_memory_source_hadith_id"), table_name="translation_memory")
    op.drop_index(op.f("ix_translation_memory_language"), table_name="translation_memory")
    op.drop_table("translation_memory")

    op.drop_index(op.f("ix_translation_glossary_version"), table_name="translation_glossary")
    op.drop_index(op.f("ix_translation_glossary_term_type"), table_name="translation_glossary")
    op.drop_index(op.f("ix_translation_glossary_term_norm"), table_name="translation_glossary")
    op.drop_index(op.f("ix_translation_glossary_policy"), table_name="translation_glossary")
    op.drop_index(op.f("ix_translation_glossary_language"), table_name="translation_glossary")
    op.drop_index(op.f("ix_translation_glossary_active"), table_name="translation_glossary")
    op.drop_table("translation_glossary")

    op.drop_index(op.f("ix_translation_segments_translation_version"), table_name="translation_segments")
    op.drop_index(op.f("ix_translation_segments_translation_id"), table_name="translation_segments")
    op.drop_index(op.f("ix_translation_segments_status"), table_name="translation_segments")
    op.drop_index(op.f("ix_translation_segments_source_sha256"), table_name="translation_segments")
    op.drop_index(op.f("ix_translation_segments_segment_kind"), table_name="translation_segments")
    op.drop_index(op.f("ix_translation_segments_risk_level"), table_name="translation_segments")
    op.drop_index(op.f("ix_translation_segments_language"), table_name="translation_segments")
    op.drop_index(op.f("ix_translation_segments_hadith_id"), table_name="translation_segments")
    op.drop_table("translation_segments")

    op.drop_index(op.f("ix_hadith_translations_translation_version"), table_name="hadith_translations")
    op.drop_index(op.f("ix_hadith_translations_status"), table_name="hadith_translations")
    op.drop_index(op.f("ix_hadith_translations_source_matn_sha256"), table_name="hadith_translations")
    op.drop_index(op.f("ix_hadith_translations_source_isnad_sha256"), table_name="hadith_translations")
    op.drop_index(op.f("ix_hadith_translations_source_full_sha256"), table_name="hadith_translations")
    op.drop_index(op.f("ix_hadith_translations_risk_level"), table_name="hadith_translations")
    op.drop_index(op.f("ix_hadith_translations_language"), table_name="hadith_translations")
    op.drop_index(op.f("ix_hadith_translations_hadith_id"), table_name="hadith_translations")
    op.drop_table("hadith_translations")
