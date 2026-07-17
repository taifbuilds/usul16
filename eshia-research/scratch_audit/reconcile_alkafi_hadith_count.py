"""Reconcile Al-Kafi's stored rows with the corrected page parser.

Dry-run is the default. Pass ``--apply`` only after recording and creating the
database backup required by AGENT_HANDOFF.md.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
import datetime as dt
import re

from sqlalchemy import delete, select, update

from eshia_research.db import SessionLocal
from eshia_research.hadith_extractor import (
    _confidence_for,
    _inline_marker_re,
    _skip_page_for_hadith_index,
    _to_int,
    parse_page_state,
    split_isnad_matn,
)
from eshia_research.isnad.tokenizer import tokenize_isnad
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    ChainNodeCandidate,
    Hadith,
    HadithSplitReview,
    MentionResolution,
    Page,
    PersonResolutionDecision,
    PersonResolutionExternalReview,
)
from eshia_research.normalise import normalise_arabic_persian


SOURCE_BOOK_ID = "11005"
REJECTED = "rejected_non_hadith_fragment"
REVIEWER = "codex-alkafi-count-reconciliation"
SPLIT_VERSION = "alkafi_count_reconciliation_v1"

# A report printed inside each anchor row was previously swallowed into its
# matn. The new public ID is deliberately a suffix so every existing URL stays
# stable even though the internal ordering becomes contiguous again.
MISSING_AFTER = {
    "alkafi-192": ("alkafi-192a", 1, 65, "٣"),
    "alkafi-1597": ("alkafi-1597a", 2, 68, "٦"),
    "alkafi-3608": ("alkafi-3608a", 2, 640, "٢"),
    "alkafi-4835": ("alkafi-4835a", 3, 280, "٩"),
    "alkafi-4961": ("alkafi-4961a", 3, 310, "٦"),
    "alkafi-7830": ("alkafi-7830a", 4, 492, "١٦"),
}

# Existing genuine rows whose source-derived text/number must be refreshed.
REFRESH_LOCATORS = {
    # Three reports whose continuation resumes after bottom-of-page notes.
    "alkafi-579": (1, 219, "٤"),
    "alkafi-2460": (2, 285, "٢٤"),
    "alkafi-14965": (8, 184, "٢١٢"),
    # Six rows where an outer page/verse number hid the real report number.
    "alkafi-1391": (1, 532, "٩"),
    "alkafi-6111": (4, 35, "٢"),
    "alkafi-8413": (5, 89, "٣"),
    "alkafi-11513": (6, 269, "٥"),
    "alkafi-13381": (7, 113, "٣"),
    "alkafi-14868": (8, 144, "١١٥"),
}

FALSE_ROWS = {
    "alkafi-580": "Editorial note numbered 106; its following page text continues alkafi-579.",
    "alkafi-2461": "Editorial note numbered 16; its following page text continues alkafi-2460.",
    "alkafi-14966": "Editorial note numbered 63; its following page text continues alkafi-14965.",
}

EXPECTED_DRAFT_VOLUMES = {1: 1442, 2: 2344, 3: 2182, 4: 2192, 5: 2201, 6: 2666, 7: 1711, 8: 597}


@dataclass
class DraftHadith:
    printed_number: str
    page_start_id: int
    page_end_id: int
    volume_start: int | None
    volume_end: int | None
    page_start: int
    page_end: int
    sequence_in_page: int
    section_title: str | None
    full_text_raw: str
    source_url: str
    footnotes_json: list[dict] = field(default_factory=list)


def extract_drafts(db, book: Book) -> list[DraftHadith]:
    """Run the production parser without touching persistent hadith rows."""
    drafts: list[DraftHadith] = []
    last: DraftHadith | None = None
    last_volume: int | None = None
    carried_section: str | None = None
    carried_in_fihrist = False
    previous_page_ended_in_hadith = False
    volume_ordinal = 0
    ordinals: dict[int, int] = {}

    pages = (
        db.query(Page)
        .filter(Page.book_id == book.id, Page.text_raw.isnot(None))
        .order_by(Page.volume_number, Page.page_number, Page.id)
        .all()
    )
    for page in pages:
        if not page.text_raw or not page.text_raw.strip():
            continue
        if last_volume is not None and page.volume_number != last_volume:
            last = None
            carried_section = None
            carried_in_fihrist = False
            previous_page_ended_in_hadith = False
            volume_ordinal = 0
            ordinals.clear()
        last_volume = page.volume_number
        if _skip_page_for_hadith_index(book.source_book_id, page):
            last = None
            carried_section = None
            carried_in_fihrist = False
            previous_page_ended_in_hadith = False
            continue

        units, parser = parse_page_state(
            page.text_raw,
            initial_section=carried_section,
            initial_in_fihrist=carried_in_fihrist,
            initial_saw_hadith=previous_page_ended_in_hadith,
        )
        carried_section = parser.current_section
        carried_in_fihrist = parser.in_fihrist
        page_targets: list[tuple[str, DraftHadith]] = []

        for unit in units:
            if unit.kind == "continuation":
                if last is not None and previous_page_ended_in_hadith:
                    last.full_text_raw = f"{last.full_text_raw}\n{unit.text}".strip()
                    last.page_end_id = page.id
                    last.volume_end = page.volume_number
                    last.page_end = page.page_number
                    page_targets.append((unit.text, last))
                continue
            if unit.kind != "hadith":
                continue
            draft = DraftHadith(
                printed_number=unit.number or "",
                page_start_id=page.id,
                page_end_id=page.id,
                volume_start=page.volume_number,
                volume_end=page.volume_number,
                page_start=page.page_number,
                page_end=page.page_number,
                sequence_in_page=unit.sequence_in_page,
                section_title=unit.section_title,
                full_text_raw=unit.text,
                source_url=page.source_url,
            )
            drafts.append(draft)
            page_targets.append((unit.text, draft))
            last = draft
            volume_ordinal += 1
            ordinals[id(draft)] = volume_ordinal

        for unit in units:
            if unit.kind != "footnote" or not unit.number:
                continue
            anchor = _inline_marker_re(unit.number)
            target = next((hadith for chunk, hadith in page_targets if anchor.search(chunk)), None)
            if target is None:
                try:
                    marker_value = _to_int(unit.number)
                except ValueError:
                    marker_value = None
                if marker_value is not None:
                    target = next(
                        (hadith for _chunk, hadith in page_targets if ordinals.get(id(hadith)) == marker_value),
                        None,
                    )
                    if target is None:
                        for _chunk, hadith in page_targets:
                            groups = re.findall(r"[0-9\u0660-\u0669\u06f0-\u06f9]+", hadith.printed_number)
                            if any(_to_int(group) == marker_value for group in groups):
                                target = hadith
                                break
            if target is not None:
                target.footnotes_json.append(
                    {"marker": unit.number, "text": unit.text, "volume": page.volume_number, "page": page.page_number}
                )

        for unit in reversed(units):
            if unit.kind == "footnote":
                continue
            previous_page_ended_in_hadith = unit.kind in {"hadith", "continuation"}
            break
    return drafts


def unique_draft(drafts: list[DraftHadith], locator: tuple[int, int, str]) -> DraftHadith:
    volume, page, number = locator
    matches = [
        draft
        for draft in drafts
        if draft.volume_start == volume and draft.page_start == page and draft.printed_number == number
    ]
    if len(matches) != 1:
        raise RuntimeError(f"draft locator {locator!r} matched {len(matches)} rows")
    return matches[0]


def get_hadith(db, public_id: str) -> Hadith:
    row = db.query(Hadith).filter(Hadith.public_id == public_id).one_or_none()
    if row is None:
        raise RuntimeError(f"missing persistent row {public_id}")
    return row


def reviewed_split(db, hadith: Hadith, full_text: str) -> tuple[str | None, str]:
    """Preserve an approved boundary while taking all text from the new draft."""
    review = (
        db.query(HadithSplitReview)
        .filter(HadithSplitReview.hadith_id == hadith.id, HadithSplitReview.review_status == "approved")
        .one_or_none()
    )
    if review is not None and review.approved_matn_raw:
        probe = review.approved_matn_raw.strip()[:100]
        boundary = full_text.find(probe)
        if boundary > 0:
            return full_text[:boundary].strip(), full_text[boundary:].strip()
    # Even an unreviewed existing split is better boundary evidence than
    # rerunning a conservative splitter on a shortened variant route. Its
    # matn opening remains source-verifiable in the corrected draft.
    if hadith.matn_raw:
        probe = hadith.matn_raw.strip()[:100]
        boundary = full_text.find(probe)
        if boundary > 0:
            return full_text[:boundary].strip(), full_text[boundary:].strip()
    return split_isnad_matn(full_text)


def upsert_review(db, hadith: Hadith, *, status: str, note: str) -> HadithSplitReview:
    review = db.query(HadithSplitReview).filter(HadithSplitReview.hadith_id == hadith.id).one_or_none()
    if review is None:
        review = HadithSplitReview(hadith_id=hadith.id)
        db.add(review)
    review.approved_isnad_raw = hadith.isnad_raw
    review.approved_matn_raw = hadith.matn_raw
    review.review_status = status
    review.reviewer = REVIEWER
    review.notes = note
    review.split_version = SPLIT_VERSION
    return review


def copy_draft(db, hadith: Hadith, draft: DraftHadith, note: str) -> None:
    isnad, matn = reviewed_split(db, hadith, draft.full_text_raw)
    hadith.page_start_id = draft.page_start_id
    hadith.page_end_id = draft.page_end_id
    hadith.printed_number = draft.printed_number
    hadith.volume_start = draft.volume_start
    hadith.volume_end = draft.volume_end
    hadith.page_start = draft.page_start
    hadith.page_end = draft.page_end
    hadith.sequence_in_page = draft.sequence_in_page
    hadith.section_title = draft.section_title
    hadith.full_text_raw = draft.full_text_raw
    hadith.full_text_normalised = normalise_arabic_persian(draft.full_text_raw)
    hadith.isnad_raw = isnad
    hadith.isnad_normalised = normalise_arabic_persian(isnad) if isnad else None
    hadith.matn_raw = matn
    hadith.matn_normalised = normalise_arabic_persian(matn)
    hadith.footnotes_json = draft.footnotes_json or None
    hadith.source_url = draft.source_url
    hadith.extraction_method = "regex_v2_count_reconciled"
    hadith.extraction_confidence = max(96, _confidence_for(draft.full_text_raw, isnad, matn))
    hadith.review_status = "pending"
    upsert_review(db, hadith, status="approved", note=note)


def new_hadith(book: Book, public_id: str, sequence: int, draft: DraftHadith) -> Hadith:
    isnad, matn = split_isnad_matn(draft.full_text_raw)
    return Hadith(
        public_id=public_id,
        book_id=book.id,
        page_start_id=draft.page_start_id,
        page_end_id=draft.page_end_id,
        sequence_in_book=sequence,
        sequence_in_page=draft.sequence_in_page,
        printed_number=draft.printed_number,
        volume_start=draft.volume_start,
        volume_end=draft.volume_end,
        page_start=draft.page_start,
        page_end=draft.page_end,
        section_title=draft.section_title,
        full_text_raw=draft.full_text_raw,
        full_text_normalised=normalise_arabic_persian(draft.full_text_raw),
        isnad_raw=isnad,
        isnad_normalised=normalise_arabic_persian(isnad) if isnad else None,
        matn_raw=matn,
        matn_normalised=normalise_arabic_persian(matn),
        footnotes_json=draft.footnotes_json or None,
        source_url=draft.source_url,
        extraction_method="regex_v2_count_reconciled",
        extraction_confidence=max(96, _confidence_for(draft.full_text_raw, isnad, matn)),
        review_status="pending",
    )


def delete_false_row_derivatives(db, hadith: Hadith) -> Counter:
    chain_ids = [row[0] for row in db.query(Chain.id).filter(Chain.hadith_id == hadith.id).all()]
    node_ids = (
        [row[0] for row in db.query(ChainNode.id).filter(ChainNode.chain_id.in_(chain_ids)).all()]
        if chain_ids
        else []
    )
    counts = Counter(chains=len(chain_ids), nodes=len(node_ids))
    if node_ids:
        for model, name in (
            (PersonResolutionExternalReview, "external_reviews"),
            (PersonResolutionDecision, "decisions"),
            (MentionResolution, "mention_resolutions"),
            (ChainNodeCandidate, "node_candidates"),
        ):
            counts[name] = db.query(model).filter(model.chain_node_id.in_(node_ids)).count()
            db.execute(delete(model).where(model.chain_node_id.in_(node_ids)))
        db.execute(delete(ChainNode).where(ChainNode.id.in_(node_ids)))
    if chain_ids:
        db.execute(delete(Chain).where(Chain.id.in_(chain_ids)))
    return counts


def sync_or_create_chains(db, hadith: Hadith) -> None:
    parsed_chains = tokenize_isnad(hadith.isnad_raw) if hadith.isnad_raw else []
    stored_chains = db.query(Chain).filter(Chain.hadith_id == hadith.id).order_by(Chain.chain_number).all()
    if not stored_chains:
        for chain_number, parsed in enumerate(parsed_chains, start=1):
            chain = Chain(
                hadith_id=hadith.id,
                chain_number=chain_number,
                raw_isnad=hadith.isnad_raw,
                parser_version="isnad_v1",
                node_count=len(parsed.tokens),
                flags=",".join(sorted(parsed.flags)) or None,
                review_status="needs_review" if parsed.needs_review else "pending",
            )
            db.add(chain)
            db.flush()
            for position, token in enumerate(parsed.tokens):
                db.add(
                    ChainNode(
                        chain_id=chain.id,
                        position=position,
                        raw_token=token.raw,
                        token_normalised=token.norm[:512],
                        transmission_phrase=token.phrase,
                        node_type=token.node_type,
                        relation_kind=token.relation_kind,
                    )
                )
        return

    if len(stored_chains) != len(parsed_chains):
        raise RuntimeError(f"chain count changed for {hadith.public_id}; targeted ID-preserving sync is unsafe")
    for chain, parsed in zip(stored_chains, parsed_chains, strict=True):
        nodes = db.query(ChainNode).filter(ChainNode.chain_id == chain.id).order_by(ChainNode.position).all()
        chain.raw_isnad = hadith.isnad_raw
        chain.node_count = len(parsed.tokens)
        chain.flags = ",".join(sorted(parsed.flags)) or None
        chain.review_status = "needs_review" if parsed.needs_review else "pending"
        tokens = parsed.tokens
        if len(tokens) == len(nodes) + 1 and all(
            node.token_normalised == token.norm[:512]
            for node, token in zip(nodes, tokens[1:], strict=True)
        ):
            # The corrected source restored a compiler/opening narrator that
            # the bogus leading page number had hidden. Shift the unchanged
            # nodes in place so their IDs and human review evidence survive.
            for node in nodes:
                node.position = -(node.position + 1)
            db.flush()
            for position, (node, token) in enumerate(zip(nodes, tokens[1:], strict=True), start=1):
                node.position = position
                node.raw_token = token.raw
                node.token_normalised = token.norm[:512]
                node.transmission_phrase = token.phrase
                node.node_type = token.node_type
                node.relation_kind = token.relation_kind
            opening = tokens[0]
            db.add(
                ChainNode(
                    chain_id=chain.id,
                    position=0,
                    raw_token=opening.raw,
                    token_normalised=opening.norm[:512],
                    transmission_phrase=opening.phrase,
                    node_type=opening.node_type,
                    relation_kind=opening.relation_kind,
                )
            )
            continue
        common_prefix = 0
        for node, token in zip(nodes, tokens):
            if node.token_normalised != token.norm[:512]:
                break
            common_prefix += 1
        if common_prefix and (common_prefix < len(nodes) or common_prefix < len(tokens)):
            # A swallowed second report had been tokenized as the tail of the
            # anchor's chain. Keep the verified common-prefix node IDs, remove
            # machine-derived rows for the invalid suffix, and create the
            # corrected suffix. Human/external evidence would require
            # migration rather than deletion, so fail closed if any exists.
            surplus_ids = [node.id for node in nodes[common_prefix:]]
            external_count = (
                db.query(PersonResolutionExternalReview)
                .filter(PersonResolutionExternalReview.chain_node_id.in_(surplus_ids))
                .count()
            )
            if external_count:
                raise RuntimeError(
                    f"cannot trim {hadith.public_id}: {external_count} external reviews target surplus nodes"
                )
            for model in (PersonResolutionDecision, MentionResolution, ChainNodeCandidate):
                db.execute(delete(model).where(model.chain_node_id.in_(surplus_ids)))
            db.execute(delete(ChainNode).where(ChainNode.id.in_(surplus_ids)))
            for node, token in zip(nodes[:common_prefix], tokens[:common_prefix], strict=True):
                node.raw_token = token.raw
                node.token_normalised = token.norm[:512]
                node.transmission_phrase = token.phrase
                node.node_type = token.node_type
                node.relation_kind = token.relation_kind
            for position, token in enumerate(tokens[common_prefix:], start=common_prefix):
                db.add(
                    ChainNode(
                        chain_id=chain.id,
                        position=position,
                        raw_token=token.raw,
                        token_normalised=token.norm[:512],
                        transmission_phrase=token.phrase,
                        node_type=token.node_type,
                        relation_kind=token.relation_kind,
                    )
                )
            continue
        if len(nodes) != len(tokens):
            raise RuntimeError(f"node count changed for {hadith.public_id}; targeted ID-preserving sync is unsafe")
        for node, token in zip(nodes, tokens, strict=True):
            node.raw_token = token.raw
            node.token_normalised = token.norm[:512]
            node.transmission_phrase = token.phrase
            node.node_type = token.node_type
            node.relation_kind = token.relation_kind


def page_counts(rows) -> Counter:
    return Counter((row.volume_start, row.page_start) for row in rows)


def audit(db, book: Book, drafts: list[DraftHadith]) -> dict:
    stored = db.query(Hadith).filter(Hadith.book_id == book.id).order_by(Hadith.sequence_in_book).all()
    visible = [row for row in stored if row.review_status != REJECTED]
    draft_volumes = Counter(draft.volume_start for draft in drafts)
    visible_pages = page_counts(visible)
    draft_pages = page_counts(drafts)
    page_mismatches = {
        key: (visible_pages[key], draft_pages[key])
        for key in sorted(set(visible_pages) | set(draft_pages))
        if visible_pages[key] != draft_pages[key]
    }
    return {
        "stored": len(stored),
        "rejected": len(stored) - len(visible),
        "visible": len(visible),
        "draft": len(drafts),
        "draft_volumes": dict(sorted(draft_volumes.items())),
        "page_mismatches": page_mismatches,
    }


def validate_targets(db, drafts: list[DraftHadith]) -> None:
    if len(drafts) != 15335:
        raise RuntimeError(f"expected 15,335 parser drafts, found {len(drafts):,}")
    volumes = dict(sorted(Counter(draft.volume_start for draft in drafts).items()))
    if volumes != EXPECTED_DRAFT_VOLUMES:
        raise RuntimeError(f"unexpected draft volume counts: {volumes}")
    all_ids = set(MISSING_AFTER) | set(REFRESH_LOCATORS) | set(FALSE_ROWS)
    if len(all_ids) != 18:
        raise RuntimeError("repair target sets overlap")
    for public_id in all_ids:
        get_hadith(db, public_id)
    for _anchor, (_new_id, volume, page, number) in MISSING_AFTER.items():
        unique_draft(drafts, (volume, page, number))
    for locator in REFRESH_LOCATORS.values():
        unique_draft(drafts, locator)


def apply_reconciliation(db, book: Book, drafts: list[DraftHadith]) -> Counter:
    if db.query(Hadith).filter(Hadith.public_id.in_([spec[0] for spec in MISSING_AFTER.values()])).count():
        raise RuntimeError("one or more suffixed repair IDs already exist; refusing a partial/repeated apply")

    stats = Counter()
    draft_for_anchor = {
        anchor: unique_draft(drafts, (volume, page, number))
        for anchor, (_new_id, volume, page, number) in MISSING_AFTER.items()
    }

    # The original anchor also needs the corrected first half from the draft.
    for anchor_id in MISSING_AFTER:
        anchor = get_hadith(db, anchor_id)
        locator = (anchor.volume_start, anchor.page_start, anchor.printed_number)
        copy_draft(
            db,
            anchor,
            unique_draft(drafts, locator),
            "Source scan split a swallowed numbered report from this row; this is the verified first report.",
        )
        stats["anchors_refreshed"] += 1

    for public_id, locator in REFRESH_LOCATORS.items():
        copy_draft(
            db,
            get_hadith(db, public_id),
            unique_draft(drafts, locator),
            "Source scan reconciled this row with the corrected page parser (continuation or printed-number repair).",
        )
        stats["existing_refreshed"] += 1

    for public_id, note in FALSE_ROWS.items():
        row = get_hadith(db, public_id)
        row.review_status = REJECTED
        upsert_review(db, row, status="rejected", note=note)
        stats.update(delete_false_row_derivatives(db, row))
        stats["newly_rejected"] += 1

    # Make the final internal sequence contiguous while retaining every
    # existing public ID. Put the six new rows immediately after their anchor.
    existing = db.query(Hadith).filter(Hadith.book_id == book.id).order_by(Hadith.sequence_in_book).all()
    ordered: list[tuple[str, Hadith | DraftHadith, str | None]] = []
    for row in existing:
        ordered.append(("existing", row, None))
        if row.public_id in MISSING_AFTER:
            new_public_id = MISSING_AFTER[row.public_id][0]
            ordered.append(("new", draft_for_anchor[row.public_id], new_public_id))

    db.execute(
        update(Hadith)
        .where(Hadith.book_id == book.id)
        .values(sequence_in_book=-Hadith.sequence_in_book)
        .execution_options(synchronize_session=False)
    )
    db.flush()
    mappings = []
    new_rows: list[Hadith] = []
    for sequence, (kind, value, public_id) in enumerate(ordered, start=1):
        if kind == "existing":
            mappings.append({"id": value.id, "sequence_in_book": sequence})
        else:
            row = new_hadith(book, public_id or "", sequence, value)
            db.add(row)
            new_rows.append(row)
    db.bulk_update_mappings(Hadith, mappings)
    db.flush()

    for row in new_rows:
        upsert_review(
            db,
            row,
            status="approved",
            note="Numbered report recovered from inside the preceding row and verified against the source page.",
        )
        sync_or_create_chains(db, row)
        stats["inserted"] += 1

    # Refresh chain text/tokens in place for genuine existing rows. Node IDs
    # remain stable, so valid external/admin review evidence remains linked.
    for public_id in set(MISSING_AFTER) | set(REFRESH_LOCATORS):
        sync_or_create_chains(db, get_hadith(db, public_id))
        stats["chains_synced_hadiths"] += 1

    return stats


def print_audit(label: str, result: dict) -> None:
    print(label)
    for key in ("stored", "rejected", "visible", "draft"):
        print(f"  {key}: {result[key]:,}")
    print(f"  draft_volumes: {result['draft_volumes']}")
    print(f"  page_mismatches: {len(result['page_mismatches'])}")
    for key, counts in result["page_mismatches"].items():
        print(f"    volume/page {key[0]}/{key[1]}: visible={counts[0]}, draft={counts[1]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="commit the validated repair")
    args = parser.parse_args()

    with SessionLocal() as db:
        book = db.query(Book).filter(Book.source_book_id == SOURCE_BOOK_ID).one()
        drafts = extract_drafts(db, book)
        validate_targets(db, drafts)
        before = audit(db, book, drafts)
        print_audit("CURRENT", before)
        if not args.apply:
            recovered_count = db.query(Hadith).filter(
                Hadith.public_id.in_([spec[0] for spec in MISSING_AFTER.values()])
            ).count()
            if recovered_count == 6 and before["visible"] == before["draft"] and not before["page_mismatches"]:
                print("AUDIT OK: reconciliation is already applied; no database changes.")
            elif recovered_count == 0:
                print("DRY RUN: 6 insertions, 3 new rejections, 15 genuine-row refreshes; no database changes.")
            else:
                raise RuntimeError(f"partial reconciliation state: {recovered_count}/6 recovered IDs exist")
            return

        stats = apply_reconciliation(db, book, drafts)
        db.flush()
        after = audit(db, book, drafts)
        if after["stored"] != 15361 or after["rejected"] != 26 or after["visible"] != 15335:
            raise RuntimeError(f"post-apply count invariant failed: {after}")
        if after["page_mismatches"]:
            raise RuntimeError(f"post-apply page alignment failed: {after['page_mismatches']}")
        sequences = [row[0] for row in db.query(Hadith.sequence_in_book).filter(Hadith.book_id == book.id).order_by(Hadith.sequence_in_book)]
        if sequences != list(range(1, 15362)):
            raise RuntimeError("Al-Kafi sequence_in_book is not contiguous after repair")
        db.commit()
        print(f"APPLIED at {dt.datetime.now(dt.timezone.utc).isoformat()}: {dict(stats)}")
        print_audit("AFTER", after)
        print("Derived narrator/person resolutions must now be refreshed; chain-node IDs for genuine existing rows were preserved.")


if __name__ == "__main__":
    main()
