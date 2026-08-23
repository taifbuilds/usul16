"""Move a book's parsed chains between two copies of the corpus, as a delta.

The sibling of `commentary.transfer`, and it exists for the same reason: the
research database is several GB, chain work happens locally, and production is
a separate copy that must not be overwritten wholesale to publish one book.

**Rows travel keyed by `public_id`, never by `hadith_id`.** Nothing guarantees
the two copies share a `hadiths.id` sequence, and a chain carrying a raw
`hadith_id` would attach someone else's isnad to the wrong report.

Two further identifiers cross the wire, and both are guarded by name rather
than trusted:

* `mention_resolutions.person_id` — a wrong value here does not fail loudly.
  It silently claims a narration was transmitted by a different man, which is
  the worst outcome this project can produce. Every referenced person travels
  with its canonical name and the import refuses unless the target agrees.
* `chain_nodes.canonical_narrator_id` — same treatment.

The split itself travels too. `chains` are derived from `hadiths.isnad_raw`,
so shipping chains without the split that produced them would leave the reader
showing one boundary and the chain layer another.

The flow mirrors the commentary one, three steps, each its own CLI command:

  1. *target*  ``chain-manifest``      -> what the target already has
  2. *source*  ``export-chain-delta``  -> only the hadiths that differ
  3. *target*  ``import-chain-delta``  -> validate everything, then one write

Every delete is scoped to the hadiths named in the delta. Production holds
88,379 human resolution decisions for al-Kafi; publishing Faqih must not be
able to reach them.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    ChainNodeCandidate,
    Hadith,
    MentionResolution,
    Narrator,
    Person,
    PersonResolutionDecision,
    PersonResolutionExternalReview,
)

TRANSFER_FORMAT = "usul16.chain-delta.v1"

# The split that produced the chains. Carried so the reader's boundary and the
# chain layer cannot disagree after a deploy.
_SPLIT_FIELDS = ("isnad_raw", "isnad_normalised", "matn_raw", "matn_normalised")

# `id` and `hadith_id` are deliberately absent: local identifiers never travel.
_CHAIN_FIELDS = (
    "chain_number",
    "raw_isnad",
    "parser_version",
    "node_count",
    "flags",
    "review_status",
)

_NODE_FIELDS = (
    "position",
    "raw_token",
    "token_normalised",
    "transmission_phrase",
    "node_type",
    "relation_kind",
    "confidence",
    "resolution_method",
    "resolution_reason",
    "review_status",
)

_RESOLUTION_FIELDS = (
    "rank",
    "status",
    "method",
    "evidence_json",
    "evidence_summary",
    "resolver_version",
)

# Identities the delta references travel with it. Resolving a chain can mint a
# person the target has never seen — a `latent` one asserted by a nasab with no
# Mu'jam entry behind it — and such a person exists only in the database that
# minted it. Without this the import would either refuse or, worse, drop the
# resolution and quietly publish a shorter chain.
#
# `primary_entry_id` is deliberately not carried: it points into `person_entries`,
# whose ids are not part of this contract. A minted person has none anyway.
_PERSON_FIELDS = (
    "canonical_name_ar",
    "canonical_name_norm",
    "kunya",
    "laqab",
    "nisba",
    "father_name_norm",
    "death_year_note",
    "generation_layer",
    "kind",
    "origin",
    "notes",
)

_NARRATOR_FIELDS = (
    "canonical_name_ar",
    "canonical_name_norm",
    "canonical_name_en",
    "kunya",
    "laqab",
    "nisba",
    "father_name",
    "death_year_note",
    "generation_layer",
    "school_or_sect",
    "summary_status",
    "notes",
)


def _canonical(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hadith_fingerprint(entry: dict[str, Any]) -> str:
    """Stable hash of everything this module would write for one hadith.

    Covers the split as well as the chains, so a re-split that leaves the
    tokenised chain identical still ships.
    """
    material = {
        "split": {field: entry["split"].get(field) for field in _SPLIT_FIELDS},
        "chains": entry["chains"],
    }
    return hashlib.sha256(_canonical(material).encode("utf-8")).hexdigest()


def _book_or_raise(db: Session, source_book_id: str) -> Book:
    book = db.scalar(select(Book).where(Book.source_book_id == source_book_id))
    if book is None:
        raise ValueError(f"No book with source_book_id={source_book_id!r} in this database")
    return book


def _collect(
    db: Session, source_book_id: str
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Everything this module would ship for a book.

    Returns the per-hadith material keyed by public_id, and the identity
    rows those hadiths reference.
    """
    book = _book_or_raise(db, source_book_id)

    hadiths = db.scalars(
        select(Hadith).where(Hadith.book_id == book.id).order_by(Hadith.sequence_in_book)
    ).all()
    by_id = {h.id: h for h in hadiths}
    if not by_id:
        return {}, {"persons": [], "narrators": []}

    chains = db.scalars(
        select(Chain).where(Chain.hadith_id.in_(list(by_id))).order_by(Chain.hadith_id, Chain.chain_number)
    ).all()
    chain_ids = [c.id for c in chains]

    nodes_by_chain: dict[int, list[ChainNode]] = {}
    node_ids: list[int] = []
    if chain_ids:
        for node in db.scalars(
            select(ChainNode).where(ChainNode.chain_id.in_(chain_ids)).order_by(ChainNode.chain_id, ChainNode.position)
        ).all():
            nodes_by_chain.setdefault(node.chain_id, []).append(node)
            node_ids.append(node.id)

    resolutions_by_node: dict[int, list[MentionResolution]] = {}
    if node_ids:
        for row in db.scalars(
            select(MentionResolution)
            .where(MentionResolution.chain_node_id.in_(node_ids))
            .order_by(MentionResolution.chain_node_id, MentionResolution.rank)
        ).all():
            resolutions_by_node.setdefault(row.chain_node_id, []).append(row)

    # Names for every referenced identity, so the target can check rather than
    # trust the ids.
    person_ids = {
        r.person_id
        for rows in resolutions_by_node.values()
        for r in rows
        if r.person_id is not None
    }
    narrator_ids = {
        n.canonical_narrator_id
        for nodes in nodes_by_chain.values()
        for n in nodes
        if n.canonical_narrator_id is not None
    }
    person_rows = (
        db.scalars(select(Person).where(Person.id.in_(list(person_ids)))).all()
        if person_ids
        else []
    )
    narrator_rows = (
        db.scalars(select(Narrator).where(Narrator.id.in_(list(narrator_ids)))).all()
        if narrator_ids
        else []
    )
    person_names = {p.id: p.canonical_name_ar for p in person_rows}
    narrator_names = {n.id: n.canonical_name_ar for n in narrator_rows}
    identities = {
        "persons": [
            {"id": p.id, **{field: getattr(p, field) for field in _PERSON_FIELDS}}
            for p in person_rows
        ],
        "narrators": [
            {"id": n.id, **{field: getattr(n, field) for field in _NARRATOR_FIELDS}}
            for n in narrator_rows
        ],
    }

    chains_by_hadith: dict[int, list[dict[str, Any]]] = {}
    for chain in chains:
        payload_nodes = []
        for node in nodes_by_chain.get(chain.id, []):
            payload_nodes.append(
                {
                    **{field: getattr(node, field) for field in _NODE_FIELDS},
                    "canonical_narrator_id": node.canonical_narrator_id,
                    "canonical_narrator_name": narrator_names.get(node.canonical_narrator_id),
                    "resolutions": [
                        {
                            **{field: getattr(row, field) for field in _RESOLUTION_FIELDS},
                            "person_id": row.person_id,
                            "person_name": person_names.get(row.person_id),
                        }
                        for row in resolutions_by_node.get(node.id, [])
                    ],
                }
            )
        chains_by_hadith.setdefault(chain.hadith_id, []).append(
            {**{field: getattr(chain, field) for field in _CHAIN_FIELDS}, "nodes": payload_nodes}
        )

    collected: dict[str, dict[str, Any]] = {}
    for hadith in hadiths:
        collected[hadith.public_id] = {
            "public_id": hadith.public_id,
            "split": {field: getattr(hadith, field) for field in _SPLIT_FIELDS},
            "chains": chains_by_hadith.get(hadith.id, []),
        }
    return collected, identities


def build_manifest(db: Session, source_book_id: str) -> dict[str, Any]:
    """Fingerprint what THIS database holds for a book. Run on the target."""
    collected, _ = _collect(db, source_book_id)
    return {
        "format": TRANSFER_FORMAT,
        "source_book_id": source_book_id,
        "entries": {pid: hadith_fingerprint(entry) for pid, entry in collected.items()},
    }


def export_delta(
    db: Session, source_book_id: str, manifest: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Export only the hadiths whose chain material differs from the target."""
    if manifest is not None:
        if manifest.get("format") != TRANSFER_FORMAT:
            raise ValueError(f"Manifest is not {TRANSFER_FORMAT}: {manifest.get('format')!r}")
        if manifest.get("source_book_id") != source_book_id:
            raise ValueError(
                "Manifest is for a different book: "
                f"{manifest.get('source_book_id')!r} != {source_book_id!r}"
            )

    collected, identities = _collect(db, source_book_id)
    known = (manifest or {}).get("entries", {})

    changed = []
    unchanged = 0
    for public_id, entry in collected.items():
        if known.get(public_id) == hadith_fingerprint(entry):
            unchanged += 1
            continue
        changed.append(entry)

    # A hadith the target has and the source no longer does is reported, never
    # deleted silently — the corpora should not diverge that way, and if they
    # have, a human needs to know before anything is removed.
    missing_locally = sorted(set(known) - set(collected))

    # Only the identities the shipped hadiths actually reference.
    referenced_persons = {
        resolution["person_id"]
        for entry in changed
        for chain in entry["chains"]
        for node in chain["nodes"]
        for resolution in node["resolutions"]
        if resolution.get("person_id") is not None
    }
    referenced_narrators = {
        node["canonical_narrator_id"]
        for entry in changed
        for chain in entry["chains"]
        for node in chain["nodes"]
        if node.get("canonical_narrator_id") is not None
    }

    return {
        "format": TRANSFER_FORMAT,
        "source_book_id": source_book_id,
        "entries": changed,
        "identities": {
            "persons": [p for p in identities["persons"] if p["id"] in referenced_persons],
            "narrators": [
                n for n in identities["narrators"] if n["id"] in referenced_narrators
            ],
        },
        "summary": {
            "changed": len(changed),
            "unchanged": unchanged,
            "total_local_hadiths": len(collected),
            "present_on_target_only": missing_locally,
        },
    }


def write_delta(delta: dict[str, Any], path: str) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(delta, handle, ensure_ascii=False)


def read_delta(path: str) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        delta = json.load(handle)
    if delta.get("format") != TRANSFER_FORMAT:
        raise ValueError(f"Not a {TRANSFER_FORMAT} file: {delta.get('format')!r}")
    return delta


def _validate(
    db: Session, delta: dict[str, Any]
) -> tuple[dict[str, Hadith], list[int], list[int]]:
    """Refuse the whole delta unless every identifier in it checks out.

    Runs before any write. Three classes of failure are fatal, and each would
    otherwise corrupt silently rather than raise: an unknown report, an
    identity the target does not have, and an identity whose id means a
    different person there.
    """
    source_book_id = delta["source_book_id"]
    book = _book_or_raise(db, source_book_id)

    entries = delta["entries"]
    public_ids = [entry["public_id"] for entry in entries]
    found = {
        h.public_id: h
        for h in db.scalars(
            select(Hadith).where(Hadith.public_id.in_(public_ids), Hadith.book_id == book.id)
        ).all()
    }
    unknown = sorted(set(public_ids) - set(found))
    if unknown:
        raise ValueError(
            f"{len(unknown)} public_id(s) are not in this database's {source_book_id}: "
            + ", ".join(unknown[:5])
            + ("…" if len(unknown) > 5 else "")
        )

    wanted_persons: dict[int, str | None] = {}
    wanted_narrators: dict[int, str | None] = {}
    for entry in entries:
        for chain in entry["chains"]:
            for node in chain["nodes"]:
                if node.get("canonical_narrator_id") is not None:
                    wanted_narrators[node["canonical_narrator_id"]] = node.get(
                        "canonical_narrator_name"
                    )
                for resolution in node["resolutions"]:
                    if resolution.get("person_id") is not None:
                        wanted_persons[resolution["person_id"]] = resolution.get("person_name")

    carried = delta.get("identities", {})

    def check(model, wanted: dict[int, str | None], label: str, section: str) -> list[int]:
        """Agree about every identity, and report the ones we must create.

        An id the target lacks is not automatically an error: resolving a
        chain can mint a person that exists only where it was minted. It is
        an error when the delta cannot supply it either, and it is always an
        error when both sides know the id and disagree about who it is.
        """
        if not wanted:
            return []
        here = {
            row.id: row.canonical_name_ar
            for row in db.scalars(select(model).where(model.id.in_(list(wanted)))).all()
        }
        mismatched = [
            f"{i} is {here[i]!r} here but {name!r} in the delta"
            for i, name in wanted.items()
            if i in here and name is not None and here[i] != name
        ]
        if mismatched:
            raise ValueError(
                f"{len(mismatched)} {label} id(s) mean a different person here — "
                "refusing, because this would misattribute narrations: "
                + "; ".join(mismatched[:3])
                + ("…" if len(mismatched) > 3 else "")
            )
        missing = sorted(set(wanted) - set(here))
        supplied = {row["id"] for row in carried.get(section, [])}
        unsupplied = [i for i in missing if i not in supplied]
        if unsupplied:
            raise ValueError(
                f"{len(unsupplied)} {label} id(s) are neither here nor carried by the "
                "delta: "
                + ", ".join(str(i) for i in unsupplied[:5])
                + ("…" if len(unsupplied) > 5 else "")
            )
        return missing

    missing_persons = check(Person, wanted_persons, "person", "persons")
    missing_narrators = check(Narrator, wanted_narrators, "narrator", "narrators")
    return found, missing_persons, missing_narrators


def import_delta(db: Session, delta: dict[str, Any], *, dry_run: bool = False) -> dict[str, int]:
    """Validate everything, then replace those hadiths' chains in one write."""
    found, missing_persons, missing_narrators = _validate(db, delta)
    entries = delta["entries"]
    carried = delta.get("identities", {})

    hadith_ids = [found[entry["public_id"]].id for entry in entries]
    stats = {
        "hadiths": len(entries),
        "chains": 0,
        "nodes": 0,
        "resolutions": 0,
        "persons_created": 0,
        "narrators_created": 0,
    }

    # Identities first: the rows below reference them.
    for section, ids, model, fields, counter in (
        ("persons", missing_persons, Person, _PERSON_FIELDS, "persons_created"),
        ("narrators", missing_narrators, Narrator, _NARRATOR_FIELDS, "narrators_created"),
    ):
        if not ids:
            continue
        supplied = {row["id"]: row for row in carried.get(section, [])}
        for identity_id in ids:
            row = supplied[identity_id]
            db.add(model(id=identity_id, **{field: row.get(field) for field in fields}))
            stats[counter] += 1
        db.flush()

    if hadith_ids:
        # Scoped to exactly the reports in this delta. Nothing else in the
        # corpus is reachable from here.
        old_chain_ids = select(Chain.id).where(Chain.hadith_id.in_(hadith_ids))
        old_node_ids = select(ChainNode.id).where(ChainNode.chain_id.in_(old_chain_ids))
        for model in (
            PersonResolutionExternalReview,
            PersonResolutionDecision,
            MentionResolution,
            ChainNodeCandidate,
        ):
            db.execute(delete(model).where(model.chain_node_id.in_(old_node_ids)))
        db.execute(delete(ChainNode).where(ChainNode.chain_id.in_(old_chain_ids)))
        db.execute(delete(Chain).where(Chain.hadith_id.in_(hadith_ids)))
        db.flush()

    for entry in entries:
        hadith = found[entry["public_id"]]
        for field, value in entry["split"].items():
            setattr(hadith, field, value)

        for chain_payload in entry["chains"]:
            chain = Chain(
                hadith_id=hadith.id,
                **{field: chain_payload[field] for field in _CHAIN_FIELDS},
            )
            db.add(chain)
            db.flush()
            stats["chains"] += 1

            for node_payload in chain_payload["nodes"]:
                node = ChainNode(
                    chain_id=chain.id,
                    canonical_narrator_id=node_payload.get("canonical_narrator_id"),
                    **{field: node_payload[field] for field in _NODE_FIELDS},
                )
                db.add(node)
                db.flush()
                stats["nodes"] += 1

                for resolution_payload in node_payload["resolutions"]:
                    db.add(
                        MentionResolution(
                            chain_node_id=node.id,
                            person_id=resolution_payload.get("person_id"),
                            **{
                                field: resolution_payload[field]
                                for field in _RESOLUTION_FIELDS
                            },
                        )
                    )
                    stats["resolutions"] += 1

    if dry_run:
        db.rollback()
    else:
        db.commit()
    return stats


def verify_target(db: Session, source_book_id: str) -> dict[str, int]:
    """Counts a human can compare against the source after an import."""
    book = _book_or_raise(db, source_book_id)
    hadith_ids = select(Hadith.id).where(Hadith.book_id == book.id)
    chain_ids = select(Chain.id).where(Chain.hadith_id.in_(hadith_ids))
    node_ids = select(ChainNode.id).where(ChainNode.chain_id.in_(chain_ids))
    return {
        "chains": db.scalar(
            select(func.count()).select_from(Chain).where(Chain.hadith_id.in_(hadith_ids))
        )
        or 0,
        "nodes": db.scalar(
            select(func.count()).select_from(ChainNode).where(ChainNode.chain_id.in_(chain_ids))
        )
        or 0,
        "resolutions": db.scalar(
            select(func.count())
            .select_from(MentionResolution)
            .where(MentionResolution.chain_node_id.in_(node_ids))
        )
        or 0,
        "needs_review": db.scalar(
            select(func.count())
            .select_from(Chain)
            .where(Chain.hadith_id.in_(hadith_ids), Chain.review_status == "needs_review")
        )
        or 0,
    }
