"""baseline the person-resolution schema missing from Alembic history

Revision ID: fa7e9c2d4b51
Revises: e4c91f7b2d68
Create Date: 2026-08-10 00:00:00.000000

The person-resolution tables were first created through ``create_all()`` on
the established corpus.  That made the application work, but it meant an
empty database upgraded through Alembic could not reproduce the schema.

This is deliberately a baseline migration: a database that already has any
of these tables is a legacy database and must be preserved.  Fresh databases
create the missing tables; existing databases simply record this revision.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "fa7e9c2d4b51"
down_revision: str | Sequence[str] | None = "e4c91f7b2d68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _create_persons() -> None:
    if _has_table("persons"):
        return
    op.create_table(
        "persons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("canonical_name_ar", sa.String(length=512), nullable=False),
        sa.Column("canonical_name_norm", sa.String(length=512), nullable=False),
        sa.Column("kunya", sa.String(length=256), nullable=True),
        sa.Column("laqab", sa.String(length=256), nullable=True),
        sa.Column("nisba", sa.String(length=256), nullable=True),
        sa.Column("father_name_norm", sa.String(length=512), nullable=True),
        sa.Column("death_year_note", sa.String(length=128), nullable=True),
        sa.Column("generation_layer", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("origin", sa.String(length=32), nullable=False),
        sa.Column("primary_entry_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["primary_entry_id"], ["rijal_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_persons_canonical_name_norm"), "persons", ["canonical_name_norm"])
    op.create_index(op.f("ix_persons_kind"), "persons", ["kind"])
    op.create_index(op.f("ix_persons_primary_entry_id"), "persons", ["primary_entry_id"])


def _create_person_entry_links() -> None:
    if _has_table("person_entry_links"):
        return
    op.create_table(
        "person_entry_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("link_type", sa.String(length=32), nullable=False),
        sa.Column("evidence_quote", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["entry_id"], ["rijal_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id", "entry_id", "link_type", name="uq_person_entry_link"),
    )
    op.create_index(op.f("ix_person_entry_links_person_id"), "person_entry_links", ["person_id"])
    op.create_index(op.f("ix_person_entry_links_entry_id"), "person_entry_links", ["entry_id"])
    op.create_index(op.f("ix_person_entry_links_link_type"), "person_entry_links", ["link_type"])


def _create_person_surface_forms() -> None:
    if _has_table("person_surface_forms"):
        return
    op.create_table(
        "person_surface_forms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("form_raw", sa.String(length=512), nullable=False),
        sa.Column("form_norm", sa.String(length=512), nullable=False),
        sa.Column("derivation", sa.String(length=32), nullable=False),
        sa.Column("shared_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id", "form_norm", name="uq_person_surface_form"),
    )
    op.create_index(op.f("ix_person_surface_forms_person_id"), "person_surface_forms", ["person_id"])
    op.create_index(op.f("ix_person_surface_forms_form_norm"), "person_surface_forms", ["form_norm"])
    op.create_index(op.f("ix_person_surface_forms_derivation"), "person_surface_forms", ["derivation"])
    op.create_index(op.f("ix_person_surface_forms_shared_count"), "person_surface_forms", ["shared_count"])


def _create_person_relations() -> None:
    if _has_table("person_relations"):
        return
    op.create_table(
        "person_relations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("related_person_id", sa.Integer(), nullable=True),
        sa.Column("relation_kind", sa.String(length=32), nullable=False),
        sa.Column("related_name_norm", sa.String(length=512), nullable=True),
        sa.Column("source_note", sa.String(length=512), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["related_person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "person_id", "relation_kind", "related_name_norm", name="uq_person_relation"
        ),
    )
    op.create_index(op.f("ix_person_relations_person_id"), "person_relations", ["person_id"])
    op.create_index(op.f("ix_person_relations_related_person_id"), "person_relations", ["related_person_id"])
    op.create_index(op.f("ix_person_relations_relation_kind"), "person_relations", ["relation_kind"])


def _create_collective_rosters() -> None:
    if _has_table("collective_rosters"):
        return
    op.create_table(
        "collective_rosters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("collective_norm", sa.String(length=512), nullable=False),
        sa.Column("keyed_by_norm", sa.String(length=512), nullable=False),
        sa.Column("member_person_id", sa.Integer(), nullable=True),
        sa.Column("member_name_ar", sa.String(length=512), nullable=False),
        sa.Column("member_name_norm", sa.String(length=512), nullable=False),
        sa.Column("source_citation", sa.String(length=512), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["member_person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "collective_norm",
            "keyed_by_norm",
            "member_name_norm",
            name="uq_collective_roster_member",
        ),
    )
    op.create_index(op.f("ix_collective_rosters_collective_norm"), "collective_rosters", ["collective_norm"])
    op.create_index(op.f("ix_collective_rosters_keyed_by_norm"), "collective_rosters", ["keyed_by_norm"])
    op.create_index(op.f("ix_collective_rosters_member_person_id"), "collective_rosters", ["member_person_id"])
    op.create_index(op.f("ix_collective_rosters_member_name_norm"), "collective_rosters", ["member_name_norm"])


def _create_person_generations() -> None:
    if _has_table("person_generations"):
        return
    op.create_table(
        "person_generations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("gen_lo", sa.Integer(), nullable=False),
        sa.Column("gen_hi", sa.Integer(), nullable=False),
        sa.Column("gen_point", sa.Integer(), nullable=True),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("resolver_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id", name="uq_person_generation"),
    )
    op.create_index(op.f("ix_person_generations_person_id"), "person_generations", ["person_id"])
    op.create_index(op.f("ix_person_generations_method"), "person_generations", ["method"])
    op.create_index(op.f("ix_person_generations_resolver_version"), "person_generations", ["resolver_version"])


def _create_mention_resolutions() -> None:
    if _has_table("mention_resolutions"):
        return
    op.create_table(
        "mention_resolutions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chain_node_id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("method", sa.String(length=64), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("resolver_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chain_node_id"], ["chain_nodes.id"]),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chain_node_id", "person_id", "resolver_version", name="uq_mention_resolution"
        ),
    )
    op.create_index(op.f("ix_mention_resolutions_chain_node_id"), "mention_resolutions", ["chain_node_id"])
    op.create_index(op.f("ix_mention_resolutions_person_id"), "mention_resolutions", ["person_id"])
    op.create_index(op.f("ix_mention_resolutions_status"), "mention_resolutions", ["status"])
    op.create_index(op.f("ix_mention_resolutions_resolver_version"), "mention_resolutions", ["resolver_version"])


def _create_person_resolution_decisions() -> None:
    if _has_table("person_resolution_decisions"):
        return
    op.create_table(
        "person_resolution_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chain_node_id", sa.Integer(), nullable=False),
        sa.Column("selected_person_id", sa.Integer(), nullable=True),
        sa.Column("decision_type", sa.String(length=64), nullable=False),
        sa.Column("confidence_tier", sa.String(length=32), nullable=False),
        sa.Column("reviewer", sa.String(length=128), nullable=False),
        sa.Column("resolver_version", sa.String(length=32), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=True),
        sa.Column("decision_summary", sa.Text(), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chain_node_id"], ["chain_nodes.id"]),
        sa.ForeignKeyConstraint(["selected_person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chain_node_id",
            "reviewer",
            "resolver_version",
            name="uq_person_resolution_decision_node_reviewer_version",
        ),
    )
    op.create_index(op.f("ix_person_resolution_decisions_chain_node_id"), "person_resolution_decisions", ["chain_node_id"])
    op.create_index(op.f("ix_person_resolution_decisions_selected_person_id"), "person_resolution_decisions", ["selected_person_id"])
    op.create_index(op.f("ix_person_resolution_decisions_decision_type"), "person_resolution_decisions", ["decision_type"])
    op.create_index(op.f("ix_person_resolution_decisions_confidence_tier"), "person_resolution_decisions", ["confidence_tier"])
    op.create_index(op.f("ix_person_resolution_decisions_reviewer"), "person_resolution_decisions", ["reviewer"])
    op.create_index(op.f("ix_person_resolution_decisions_resolver_version"), "person_resolution_decisions", ["resolver_version"])


def _create_person_resolution_external_reviews() -> None:
    if _has_table("person_resolution_external_reviews"):
        return
    op.create_table(
        "person_resolution_external_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("decision_id", sa.Integer(), nullable=True),
        sa.Column("chain_node_id", sa.Integer(), nullable=False),
        sa.Column("matched_person_id", sa.Integer(), nullable=True),
        sa.Column("case_id", sa.String(length=256), nullable=False),
        sa.Column("source_label", sa.String(length=256), nullable=False),
        sa.Column("external_reviewer", sa.String(length=128), nullable=False),
        sa.Column("verdict", sa.String(length=64), nullable=False),
        sa.Column("confidence_raw", sa.String(length=256), nullable=True),
        sa.Column("confidence_tier", sa.String(length=32), nullable=True),
        sa.Column("correct_person_text", sa.Text(), nullable=True),
        sa.Column("evidence_consulted", sa.Text(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("raw_case_text", sa.Text(), nullable=False),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["person_resolution_decisions.id"]),
        sa.ForeignKeyConstraint(["chain_node_id"], ["chain_nodes.id"]),
        sa.ForeignKeyConstraint(["matched_person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chain_node_id",
            "source_label",
            "case_id",
            name="uq_person_resolution_external_review_case",
        ),
    )
    op.create_index(op.f("ix_person_resolution_external_reviews_decision_id"), "person_resolution_external_reviews", ["decision_id"])
    op.create_index(op.f("ix_person_resolution_external_reviews_chain_node_id"), "person_resolution_external_reviews", ["chain_node_id"])
    op.create_index(op.f("ix_person_resolution_external_reviews_matched_person_id"), "person_resolution_external_reviews", ["matched_person_id"])
    op.create_index(op.f("ix_person_resolution_external_reviews_case_id"), "person_resolution_external_reviews", ["case_id"])
    op.create_index(op.f("ix_person_resolution_external_reviews_source_label"), "person_resolution_external_reviews", ["source_label"])
    op.create_index(op.f("ix_person_resolution_external_reviews_verdict"), "person_resolution_external_reviews", ["verdict"])
    op.create_index(op.f("ix_person_resolution_external_reviews_confidence_tier"), "person_resolution_external_reviews", ["confidence_tier"])


def upgrade() -> None:
    _create_persons()
    _create_person_entry_links()
    _create_person_surface_forms()
    _create_person_relations()
    _create_collective_rosters()
    _create_person_generations()
    _create_mention_resolutions()
    _create_person_resolution_decisions()
    _create_person_resolution_external_reviews()


def downgrade() -> None:
    """Keep the baseline tables when rolling an established database back.

    These tables predate this revision on existing deployments.  Alembic cannot
    distinguish those legacy tables from tables made by a fresh upgrade, so
    dropping them here could destroy editorial identity data.  This baseline is
    intentionally forward-only; use a disposable database for schema teardown.
    """
    pass
