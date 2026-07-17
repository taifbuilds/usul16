"""Repair and adjudicate every currently flagged Al-Kafi chain.

Dry-run is the default. The apply path preserves chain/node IDs whenever the
verified token sequence is unchanged and refuses to destroy external/admin
evidence. Complex ``جميعاً`` convergences retain their raw isnad and flag but
receive a reviewed-complex status instead of pretending a guessed topology is
certain.
"""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt

from sqlalchemy import delete

from eshia_research.db import SessionLocal
from eshia_research.hadith_extractor import split_isnad_matn
from eshia_research.isnad.tokenizer import REVIEW_FLAGS, tokenize_isnad
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    ChainNodeCandidate,
    Hadith,
    HadithSplitReview,
    MentionResolution,
    PersonResolutionDecision,
    PersonResolutionExternalReview,
)
from eshia_research.normalise import normalise_arabic_persian

from reconcile_alkafi_hadith_count import copy_draft, extract_drafts, unique_draft


SOURCE_BOOK_ID = "11005"
REVIEWER = "codex-alkafi-flagged-chain-audit"
VERSION = "alkafi_flagged_chain_audit_v1"

# These unreviewed rows become strictly cleaner under the corrected splitter;
# every proposal is revalidated at runtime before it can be written.
AUTO_IDS = (
    "alkafi-439", "alkafi-512", "alkafi-552", "alkafi-754", "alkafi-851",
    "alkafi-1127", "alkafi-1129", "alkafi-1172", "alkafi-2915", "alkafi-3891",
    "alkafi-5708", "alkafi-5875", "alkafi-5881", "alkafi-6160", "alkafi-6164",
    "alkafi-6351", "alkafi-6451", "alkafi-6546", "alkafi-6612", "alkafi-6983",
    "alkafi-7567", "alkafi-7862", "alkafi-8580", "alkafi-8793", "alkafi-8856",
    "alkafi-9285", "alkafi-9637", "alkafi-9639", "alkafi-9743", "alkafi-9766",
    "alkafi-9852", "alkafi-10029", "alkafi-10224", "alkafi-10683", "alkafi-10793",
    "alkafi-11084", "alkafi-13100", "alkafi-13112", "alkafi-13519", "alkafi-13551",
    "alkafi-13683", "alkafi-13821", "alkafi-13939", "alkafi-14376", "alkafi-14577",
    "alkafi-14583", "alkafi-14850", "alkafi-14955", "alkafi-15244",
)

# Explicit first words of matn, checked against the complete source text.
# The prefix before each marker is the full isnad/report-introduction retained
# by the edition; the marker and everything after it is matn.
MANUAL_MATN_START = {
    "alkafi-229": "أَنَّهُ كَتَبَ إِلَى الرَّجُلِ",
    "alkafi-344": "أَنَّ أَمِيرَ الْمُؤْمِنِينَ ع اسْتَنْهَضَ",
    "alkafi-361": "سَأَلْتُهُ عَنْ قَوْلِ اللَّهِ",
    "alkafi-402": "إِنَّ اللَّهَ أَرْحَمُ بِخَلْقِهِ",
    "alkafi-603": "فِي حَدِيثِ بُرَيْهٍ",
    "alkafi-676": "إِنِّي لَأَعْلَمُ مَا فِي السَّمَاوَاتِ",
    "alkafi-808": "بِنَحْوٍ مِنْ هَذَا إِلَّا أَنَّهُ",
    "alkafi-906": "سَأَلْتُ أَبَا جَعْفَرٍ مُحَمَّدَ بْنَ عَلِيٍّ",
    "alkafi-931": "أَنَّ زَيْدَ بْنَ عَلِيِّ بْنِ الْحُسَيْنِ",
    "alkafi-1076": "فِي احْتِجَاجِ أَمِيرِ الْمُؤْمِنِينَ",
    "alkafi-1325": "كَانَ أَحْمَدُ بْنُ عُبَيْدِ اللَّهِ بْنِ خَاقَانَ",
    "alkafi-2108": "أَيُّمَا مُؤْمِنٍ خَرَجَ إِلَى أَخِيهِ",
    "alkafi-2945": "إِنَّهُ وَ اللَّهِ مَا خَرَجَ عَبْدٌ",
    "alkafi-3285": "أَنَّهُ كَانَ يَقُولُ- اللَّهُمَّ",
    "alkafi-3318": "أَنَّ شِهَابَ بْنَ عَبْدِ رَبِّهِ",
    "alkafi-3674": "كُنَّا جُلُوساً عِنْدَ أَبِي عَبْدِ اللَّهِ",
    "alkafi-3917": "أَنَّهُمَا سَأَلَا أَبَا جَعْفَرٍ",
    "alkafi-5174": "قُلْنَا لَهُ‌[1] الرَّجُلُ يَشُكُّ",
    "alkafi-5194": "أَنَّ النَّبِيَّ ص سَمِعَ خَلْفَهُ",
    "alkafi-5229": "قُلْنَا لَهُ",
    "alkafi-5760": "ذَكَرْنَا لَهُ الْكُوفَةَ",
    "alkafi-5762": "أَنَّهُمَا قَالا لَهُ هَذِهِ الْأَرْضُ",
    "alkafi-5875": "فِي الرَّجُلِ يَكُونُ فِي بَعْضِ هَذِهِ الْأَهْوَاءِ",
    "alkafi-5932": "سَمِعْتُ أَبَا عَبْدِ اللَّهِ ع يَقُولُ",
    "alkafi-6064": "أَنَّ أَمِيرَ الْمُؤْمِنِينَ صَلَوَاتُ اللَّهِ عَلَيْهِ بَعَثَ",
    "alkafi-6148": "أَنَّ أَمِيرَ الْمُؤْمِنِينَ صَلَوَاتُ اللَّهِ عَلَيْهِ سَمِعَ",
    "alkafi-6205": "فِي قَوْلِهِ تَعَالَى- وَ الَّذِينَ",
    "alkafi-6501": "سَأَلْتُهُ عَنْ مُسَافِرٍ",
    "alkafi-6701": "أَنَّ اللَّهَ تَبَارَكَ وَ تَعَالَى أَوْحَى",
    "alkafi-6737": "إِنَّمَا هَدَمَتْ قُرَيْشٌ الْكَعْبَةَ",
    "alkafi-7117": "حَجُّوا بِامْرَأَةٍ مَعَهُمْ",
    "alkafi-7326": "سَأَلْتُهُ عَنِ الْمُحْرِمِ يَمُوتُ",
    "alkafi-7921": "إِنْ بَاتَ بِمَكَّةَ فَعَلَيْهِ دَمٌ",
    "alkafi-9232": "قَالَ رَسُولُ اللَّهِ ص",
    "alkafi-9480": "أَنَّ عَلِيَّ بْنَ الْحُسَيْنِ ع تَزَوَّجَ",
    "alkafi-9578": "الْحَمْدُ لِلَّهِ وَ صَلَّى اللَّهُ عَلَى مُحَمَّدٍ",
    "alkafi-9700": "أَنَّ ضُرَيْساً كَانَتْ تَحْتَهُ بِنْتُ حُمْرَانَ",
    "alkafi-9831": "الذِّمِّيُّ تَكُونُ لَهُ الْمَرْأَةُ الذِّمِّيَّةُ",
    "alkafi-10405": "أَنَّهُ وَفَدَ إِلَى هِشَامِ بْنِ عَبْدِ الْمَلِكِ",
    "alkafi-10676": "فِي رَجُلٍ يُطَلِّقُ امْرَأَتَهُ تَطْلِيقَةً",
    "alkafi-10720": "فِي الرَّجُلِ يُطَلِّقُ الصَّبِيَّةَ",
    "alkafi-11043": "فِي رَجُلٍ لَاعَنَ امْرَأَتَهُ",
    "alkafi-11175": "فِي أُمِّ وَلَدٍ لَيْسَ لَهَا وَلَدٌ",
    "alkafi-12571": "قُلْنَا جُعِلْنَا فِدَاكَ أَ يُكْرَهُ",
    "alkafi-13092": "أَنَّ رَجُلًا كَانَ بِهَمَذَانَ",
    "alkafi-13219": "سَأَلْنَاهُ عَنْ صَدَقَةِ رَسُولِ اللَّهِ",
    "alkafi-13260": "عَنْ رَجُلٍ أَوْصَى إِلَى رَجُلٍ",
    "alkafi-13718": "إِنْ كَانَتِ الْبَهِيمَةُ لِلْفَاعِلِ",
    "alkafi-14067": "سَأَلْنَاهُ عَنْ رَجُلٍ ضَرَبَ رَجُلًا",
    "alkafi-14098": "أَنَّ قَوْماً احْتَفَرُوا زُبْيَةً لِلْأَسَدِ",
    "alkafi-14238": "[أَنَّهُ قَالَ‌] فِي الْعَيْنِ الْعَوْرَاءِ",
    "alkafi-14674": "فِي قَوْلِ اللَّهِ عَزَّ وَ جَل",
    "alkafi-14831": "أَنَّهُمْ قَالُوا حِينَ دَخَلُوا عَلَيْهِ",
    "alkafi-14999": "فِي قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- أَ جَعَلْتُمْ",
    "alkafi-15132": "أَنَّ رَسُولَ اللَّهِ ص لَمَّا خَرَجَ مِنَ الْغَارِ",
    "alkafi-15171": "أَنَّهُ سَمِعَ عَبْدَ اللَّهِ بْنَ عَطَاءٍ",
    "alkafi-15291": "فِي قَوْلِ اللَّهِ عَزَّ وَ جَلَّ- وَ مَنْ يُرِدْ",
    "alkafi-15349": "أَنَّ إِبْرَاهِيمَ ع خَرَجَ ذَاتَ يَوْمٍ",
}

# Their stored split is already source-correct; the tokenizer cannot flatten
# the explicit alternative route without inventing a convergence. Keep the
# raw text and record a reviewed structural exception.
REVIEWED_COMPLEX_IDS = {"alkafi-3512", "alkafi-4624"}


def get_hadith(db, public_id: str) -> Hadith:
    row = db.query(Hadith).filter(Hadith.public_id == public_id).one_or_none()
    if row is None:
        raise RuntimeError(f"missing {public_id}")
    return row


def active_flags(isnad: str | None) -> Counter:
    return Counter(
        flag
        for chain in (tokenize_isnad(isnad) if isnad else [])
        for flag in chain.flags & REVIEW_FLAGS
    )


def set_split(hadith: Hadith, isnad: str | None, matn: str) -> None:
    hadith.isnad_raw = isnad or None
    hadith.isnad_normalised = normalise_arabic_persian(isnad) if isnad else None
    hadith.matn_raw = matn.strip()
    hadith.matn_normalised = normalise_arabic_persian(hadith.matn_raw)


def approve_review(db, hadith: Hadith, note: str) -> None:
    review = db.query(HadithSplitReview).filter(HadithSplitReview.hadith_id == hadith.id).one_or_none()
    if review is None:
        review = HadithSplitReview(hadith_id=hadith.id)
        db.add(review)
    review.approved_isnad_raw = hadith.isnad_raw
    review.approved_matn_raw = hadith.matn_raw
    review.review_status = "approved"
    review.reviewer = REVIEWER
    review.notes = note
    review.split_version = VERSION


def delete_node_derivatives(db, node_ids: list[int], *, allow_admin: bool = False) -> None:
    if not node_ids:
        return
    external = db.query(PersonResolutionExternalReview).filter(
        PersonResolutionExternalReview.chain_node_id.in_(node_ids)
    ).count()
    admin = db.query(PersonResolutionDecision).filter(
        PersonResolutionDecision.chain_node_id.in_(node_ids),
        PersonResolutionDecision.reviewer == "codex-admin-external-v1",
    ).count()
    if (external or admin) and not allow_admin:
        raise RuntimeError(f"refusing to delete {external} external reviews / {admin} admin decisions")
    db.execute(delete(PersonResolutionExternalReview).where(PersonResolutionExternalReview.chain_node_id.in_(node_ids)))
    db.execute(delete(PersonResolutionDecision).where(PersonResolutionDecision.chain_node_id.in_(node_ids)))
    db.execute(delete(MentionResolution).where(MentionResolution.chain_node_id.in_(node_ids)))
    db.execute(delete(ChainNodeCandidate).where(ChainNodeCandidate.chain_node_id.in_(node_ids)))


def compatible_token(old: str, new: str) -> bool:
    """Return true when a token is unchanged or only has a trimmed suffix."""

    return old == new or old.startswith(f"{new} ") or new.startswith(f"{old} ")


def chain_match_score(nodes: list[ChainNode], parsed) -> int:
    """Score a stored route against a freshly parsed route.

    Exact positional matches dominate; a cleaned matn suffix is still a safe
    route match but scores lower. This keeps reviewed IDs attached when route
    expansion changes the number/order of parallel chains.
    """

    score = 0
    for node, token in zip(nodes, parsed.tokens):
        new = token.norm[:512]
        if node.token_normalised == new:
            score += 10
        elif compatible_token(node.token_normalised, new):
            score += 4
    return score - abs(len(nodes) - len(parsed.tokens))


def update_node_surface(node: ChainNode, token) -> None:
    node.raw_token = token.raw
    node.token_normalised = token.norm[:512]
    node.transmission_phrase = token.phrase
    node.node_type = token.node_type
    node.relation_kind = token.relation_kind


def clear_legacy_resolution(node: ChainNode) -> None:
    node.canonical_narrator_id = None
    node.confidence = None
    node.resolution_method = None
    node.resolution_reason = None
    node.review_status = "pending"


def human_evidence(db, node: ChainNode):
    external = db.query(PersonResolutionExternalReview).filter(
        PersonResolutionExternalReview.chain_node_id == node.id
    ).all()
    admin = db.query(PersonResolutionDecision).filter(
        PersonResolutionDecision.chain_node_id == node.id,
        PersonResolutionDecision.reviewer == "codex-admin-external-v1",
    ).all()
    return external, admin


def retire_node_evidence(db, node: ChainNode, audit: dict, reason: str) -> None:
    external, admin = human_evidence(db, node)
    if external or admin:
        audit["retired_external"] += len(external)
        audit["retired_admin"] += len(admin)
        audit["retired_cases"].extend(row.case_id for row in external)
        audit["retirement_reasons"].add(reason)
    delete_node_derivatives(db, [node.id], allow_admin=True)


def refresh_changed_node(db, node: ChainNode, token, audit: dict) -> None:
    """Reset stale derived data while preserving safe identity decisions."""

    old = node.token_normalised
    new = token.norm[:512]
    external, admin = human_evidence(db, node)
    identity_bearing = bool(external or admin) and all(
        row.matched_person_id is not None for row in external
    ) and all(row.selected_person_id is not None for row in admin)
    safe_identity_cleanup = old.startswith(f"{new} ") and identity_bearing

    if safe_identity_cleanup:
        keep_decision_ids = {row.id for row in admin}
        keep_decision_ids.update(row.decision_id for row in external if row.decision_id is not None)
        query = delete(PersonResolutionDecision).where(PersonResolutionDecision.chain_node_id == node.id)
        if keep_decision_ids:
            query = query.where(PersonResolutionDecision.id.not_in(keep_decision_ids))
        db.execute(query)
        db.execute(delete(MentionResolution).where(MentionResolution.chain_node_id == node.id))
        db.execute(delete(ChainNodeCandidate).where(ChainNodeCandidate.chain_node_id == node.id))
        audit["preserved_identity_nodes"] += 1
    else:
        retire_node_evidence(db, node, audit, "corrected token no longer supports the old review case")

    clear_legacy_resolution(node)
    update_node_surface(node, token)


def migrate_identity_evidence(db, source: ChainNode, target: ChainNode, audit: dict) -> None:
    """Move identity-bearing human evidence off a duplicate obsolete route."""

    if source.token_normalised != target.token_normalised:
        return

    external, admin = human_evidence(db, source)
    decision_map: dict[int, int] = {}
    for decision in admin:
        if decision.selected_person_id is None:
            continue
        existing = db.query(PersonResolutionDecision).filter(
            PersonResolutionDecision.chain_node_id == target.id,
            PersonResolutionDecision.reviewer == decision.reviewer,
            PersonResolutionDecision.resolver_version == decision.resolver_version,
        ).one_or_none()
        if existing is not None:
            if existing.selected_person_id != decision.selected_person_id:
                raise RuntimeError(
                    f"conflicting reviewed identities while merging nodes {source.id} -> {target.id}"
                )
            decision_map[decision.id] = existing.id
            for review in external:
                if review.decision_id == decision.id:
                    review.decision_id = existing.id
            db.delete(decision)
            db.flush()
            audit["deduplicated_admin"] += 1
        else:
            decision.chain_node_id = target.id
            db.flush()
            decision_map[decision.id] = decision.id
            audit["migrated_admin"] += 1

    for review in external:
        if review.matched_person_id is None:
            continue
        if review.decision_id in decision_map:
            review.decision_id = decision_map[review.decision_id]
        elif review.decision_id is not None:
            linked = db.get(PersonResolutionDecision, review.decision_id)
            if linked is not None and linked.chain_node_id == source.id:
                review.decision_id = None
        review.chain_node_id = target.id
        audit["migrated_external"] += 1
    db.flush()


def append_evidence_audit(db, hadith: Hadith, audit: dict) -> None:
    if not any(value for key, value in audit.items() if key != "retired_cases" and key != "retirement_reasons"):
        return
    review = db.query(HadithSplitReview).filter(HadithSplitReview.hadith_id == hadith.id).one_or_none()
    if review is None:
        review = HadithSplitReview(
            hadith_id=hadith.id,
            approved_isnad_raw=hadith.isnad_raw,
            approved_matn_raw=hadith.matn_raw,
            review_status="approved",
            reviewer=REVIEWER,
            split_version=VERSION,
        )
        db.add(review)
    summary = (
        "Evidence-safe node reconciliation: "
        f"preserved_identity_nodes={audit['preserved_identity_nodes']}; "
        f"migrated_external={audit['migrated_external']}; migrated_admin={audit['migrated_admin']}; "
        f"deduplicated_admin={audit['deduplicated_admin']}; "
        f"retired_external={audit['retired_external']}; retired_admin={audit['retired_admin']}."
    )
    if audit["retired_cases"]:
        summary += " Retired parser-artifact cases: " + ", ".join(sorted(audit["retired_cases"])) + "."
    review.notes = f"{review.notes}\n{summary}" if review.notes else summary


def add_chain(db, hadith: Hadith, chain_number: int, parsed, *, flags: str | None = None, status: str = "approved") -> Chain:
    chain = Chain(
        hadith_id=hadith.id,
        chain_number=chain_number,
        raw_isnad=hadith.isnad_raw,
        parser_version="isnad_v1",
        node_count=len(parsed.tokens),
        flags=flags if flags is not None else (",".join(sorted(parsed.flags)) or None),
        review_status=status,
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
    return chain


def sync_chains(db, hadith: Hadith) -> None:
    fresh = tokenize_isnad(hadith.isnad_raw) if hadith.isnad_raw else []
    stored = db.query(Chain).filter(Chain.hadith_id == hadith.id).order_by(Chain.chain_number).all()
    stored_nodes = {
        chain.id: db.query(ChainNode)
        .filter(ChainNode.chain_id == chain.id)
        .order_by(ChainNode.position)
        .all()
        for chain in stored
    }
    audit = {
        "preserved_identity_nodes": 0,
        "migrated_external": 0,
        "migrated_admin": 0,
        "deduplicated_admin": 0,
        "retired_external": 0,
        "retired_admin": 0,
        "retired_cases": [],
        "retirement_reasons": set(),
    }

    # Route expansion can reorder existing parallel paths (for example, a
    # two-by-two co-narrator expansion). Match by content before assigning the
    # canonical fresh route numbers so reviewed IDs follow the same route.
    candidates = sorted(
        (
            (chain_match_score(stored_nodes[chain.id], parsed), chain, fresh_index)
            for chain in stored
            for fresh_index, parsed in enumerate(fresh)
        ),
        key=lambda item: (-item[0], item[1].chain_number, item[2]),
    )
    matched_stored: set[int] = set()
    matched_fresh: set[int] = set()
    fresh_to_chain: dict[int, Chain] = {}
    for score, chain, fresh_index in candidates:
        chain_id = chain.id
        if score <= 0 or chain_id in matched_stored or fresh_index in matched_fresh:
            continue
        matched_stored.add(chain_id)
        matched_fresh.add(fresh_index)
        fresh_to_chain[fresh_index] = chain

    # Vacate positive chain numbers first; this avoids unique-key collisions
    # when a retained route moves from (say) route 2 to route 3.
    for chain in stored:
        chain.chain_number = -chain.id
    db.flush()

    for index, parsed in enumerate(fresh):
        chain = fresh_to_chain.get(index)
        if chain is None:
            add_chain(db, hadith, index + 1, parsed)
            continue

        nodes = stored_nodes[chain.id]
        overlap = min(len(nodes), len(parsed.tokens))
        for position in range(overlap):
            node = nodes[position]
            token = parsed.tokens[position]
            if node.token_normalised == token.norm[:512]:
                update_node_surface(node, token)
            else:
                refresh_changed_node(db, node, token, audit)

        for node in nodes[overlap:]:
            retire_node_evidence(db, node, audit, "node was non-isnad text removed by the corrected split")
            db.delete(node)
        if len(nodes) > overlap:
            db.flush()

        for position, token in enumerate(parsed.tokens[overlap:], start=overlap):
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
        chain.chain_number = index + 1
        chain.raw_isnad = hadith.isnad_raw
        chain.node_count = len(parsed.tokens)
        chain.flags = ",".join(sorted(parsed.flags)) or None
        chain.review_status = "approved" if not (parsed.flags & REVIEW_FLAGS) else "needs_review"

    for chain in stored:
        if chain.id in matched_stored:
            continue
        nodes = stored_nodes[chain.id]
        target_chain = None
        if fresh_to_chain:
            _score, target_chain = max(
                (
                    (chain_match_score(nodes, fresh[fresh_index]), retained)
                    for fresh_index, retained in fresh_to_chain.items()
                ),
                key=lambda item: item[0],
            )
        targets = stored_nodes[target_chain.id] if target_chain is not None else []
        target_limit = min(len(targets), target_chain.node_count) if target_chain is not None else 0
        for position, node in enumerate(nodes):
            target = targets[position] if position < target_limit else None
            if target is not None and node.token_normalised == target.token_normalised:
                migrate_identity_evidence(db, node, target, audit)
            retire_node_evidence(db, node, audit, "duplicate route created by the former false-positive expansion")
        db.execute(delete(ChainNode).where(ChainNode.chain_id == chain.id))
        db.delete(chain)

    append_evidence_audit(db, hadith, audit)


def repair_4680(db, book: Book, drafts) -> None:
    hadith = get_hadith(db, "alkafi-4680")
    draft = unique_draft(drafts, (3, 233, "٢"))
    copy_draft(db, hadith, draft, "Removed flattened outer page number and restored printed report number 2.")
    db.flush()
    approve_review(db, hadith, "Source-restored two-route isnad; both routes manually tokenized without the false shared prefix.")

    route1 = "سَهْلُ بْنُ زِيَادٍ عَنِ الْحَسَنِ بْنِ عَلِيٍّ عَنْ بَشِيرٍ الدَّهَّانِ عَنْ أَبِي عَبْدِ اللَّهِ ع"
    route2 = "عَلِيُّ بْنُ إِبْرَاهِيمَ عَنْ مُحَمَّدِ بْنِ عِيسَى عَنْ يُونُسَ عَنْ أَبِي جَمِيلَةَ عَنْ جَابِرٍ عَنْ أَبِي جَعْفَرٍ ع"
    parsed = [tokenize_isnad(route1)[0], tokenize_isnad(route2)[0]]
    stored = db.query(Chain).filter(Chain.hadith_id == hadith.id).all()
    node_ids = [
        node.id
        for chain in stored
        for node in db.query(ChainNode).filter(ChainNode.chain_id == chain.id).all()
    ]
    delete_node_derivatives(db, node_ids)
    db.execute(delete(ChainNode).where(ChainNode.id.in_(node_ids)))
    db.execute(delete(Chain).where(Chain.hadith_id == hadith.id))
    db.flush()
    for number, chain in enumerate(parsed, start=1):
        add_chain(db, hadith, number, chain, flags="manual_multi_route", status="approved")


def prospective(db, book: Book) -> tuple[dict[str, tuple[str | None, str, str]], list[str]]:
    changes: dict[str, tuple[str | None, str, str]] = {}
    for public_id in AUTO_IDS:
        hadith = get_hadith(db, public_id)
        old_flags = active_flags(hadith.isnad_raw)
        isnad, matn = split_isnad_matn(hadith.full_text_raw)
        new_flags = active_flags(isnad)
        if isnad == hadith.isnad_raw or sum(new_flags.values()) > sum(old_flags.values()):
            raise RuntimeError(f"automatic proposal is stale or worsens {public_id}: {old_flags} -> {new_flags}")
        changes[public_id] = (isnad, matn, f"Corrected splitter reduced chain warnings {dict(old_flags)} -> {dict(new_flags)}.")

    for public_id, marker in MANUAL_MATN_START.items():
        hadith = get_hadith(db, public_id)
        position = hadith.full_text_raw.find(marker)
        if position <= 0 or hadith.full_text_raw.find(marker, position + 1) >= 0:
            raise RuntimeError(f"manual boundary for {public_id} is missing or non-unique: {marker!r}")
        isnad = hadith.full_text_raw[:position].strip()
        matn = hadith.full_text_raw[position:].strip()
        remaining = active_flags(isnad)
        non_multi = Counter({key: value for key, value in remaining.items() if key != "multi_route"})
        if non_multi:
            raise RuntimeError(f"manual boundary leaves non-structural flags for {public_id}: {non_multi}")
        changes[public_id] = (isnad, matn, f"Manual source boundary at {marker!r}; remaining flags={dict(remaining)}.")

    return changes, sorted(REVIEWED_COMPLEX_IDS)


def adjudicate_statuses(db, book: Book) -> Counter:
    result = Counter()
    approved_hadith_ids = {
        row[0]
        for row in db.query(HadithSplitReview.hadith_id)
        .filter(HadithSplitReview.review_status == "approved")
        .all()
    }
    chains = (
        db.query(Chain)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .filter(Hadith.book_id == book.id, Hadith.review_status != "rejected_non_hadith_fragment")
        .all()
    )
    for chain in chains:
        active = set((chain.flags or "").split(",")) & REVIEW_FLAGS
        active.discard("")
        if not active:
            if chain.review_status != "approved":
                chain.review_status = "pending"
            result[chain.review_status] += 1
        elif active == {"multi_route"}:
            chain.review_status = "reviewed_complex"
            result["reviewed_complex"] += 1
        elif chain.hadith_id in approved_hadith_ids:
            chain.review_status = "reviewed_exception"
            result["reviewed_exception"] += 1
        else:
            chain.review_status = "needs_review"
            result["needs_review"] += 1
    return result


def repair_external_decision_links(db, book: Book) -> Counter:
    """Repair the inherited dangling decision_id on Al-Kafi review evidence.

    Every imported external review already has exactly one promoted admin
    decision on the same node. Earlier refreshes regenerated the decision rows
    without reconnecting this optional audit pointer, which made SQLite's
    foreign-key check report every external review even though its node link
    was valid.
    """

    decisions = (
        db.query(PersonResolutionDecision)
        .join(ChainNode, ChainNode.id == PersonResolutionDecision.chain_node_id)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .filter(
            Hadith.book_id == book.id,
            PersonResolutionDecision.reviewer == "codex-admin-external-v1",
        )
        .all()
    )
    by_node: dict[int, PersonResolutionDecision] = {}
    for decision in decisions:
        if decision.chain_node_id in by_node:
            raise RuntimeError(f"multiple admin decisions for node {decision.chain_node_id}")
        by_node[decision.chain_node_id] = decision

    reviews = (
        db.query(PersonResolutionExternalReview)
        .join(ChainNode, ChainNode.id == PersonResolutionExternalReview.chain_node_id)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .filter(Hadith.book_id == book.id)
        .all()
    )
    result = Counter(total=len(reviews))
    for review in reviews:
        decision = by_node.get(review.chain_node_id)
        if decision is None:
            raise RuntimeError(f"external review {review.id} has no promoted admin decision")
        if review.decision_id != decision.id:
            review.decision_id = decision.id
            result["relinked"] += 1
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with SessionLocal() as db:
        book = db.query(Book).filter(Book.source_book_id == SOURCE_BOOK_ID).one()
        flagged_hadith_ids = {
            row[0]
            for row in db.query(Chain.hadith_id)
            .join(Hadith, Hadith.id == Chain.hadith_id)
            .filter(Hadith.book_id == book.id, Chain.review_status == "needs_review")
            .distinct()
            .all()
        }
        changes, complex_ids = prospective(db, book)
        print(f"validated split repairs={len(changes)}; explicit complex approvals={len(complex_ids)}; source repair=alkafi-4680")
        print("prospective flags", Counter(flag for isnad, _matn, _note in changes.values() for flag in active_flags(isnad).elements()))
        if not args.apply:
            print("DRY RUN: no database changes")
            return

        now = dt.datetime.now(dt.timezone.utc)
        for public_id, (isnad, matn, note) in changes.items():
            hadith = get_hadith(db, public_id)
            set_split(hadith, isnad, matn)
            hadith.updated_at = now
            approve_review(db, hadith, note)
            sync_chains(db, hadith)
        for public_id in complex_ids:
            hadith = get_hadith(db, public_id)
            approve_review(db, hadith, "Reviewed alternative-route isnad; raw source is authoritative and convergence is intentionally not guessed.")
        db.flush()

        already_synced = {get_hadith(db, public_id).id for public_id in changes}
        source_repair_id = get_hadith(db, "alkafi-4680").id
        for hadith_id in sorted(flagged_hadith_ids - already_synced - {source_repair_id}):
            sync_chains(db, db.get(Hadith, hadith_id))

        drafts = extract_drafts(db, book)
        repair_4680(db, book, drafts)
        db.flush()
        statuses = adjudicate_statuses(db, book)
        if statuses["needs_review"]:
            raise RuntimeError(f"{statuses['needs_review']} chains remain genuinely unreviewed")
        review_links = repair_external_decision_links(db, book)
        db.commit()
        print(
            "APPLIED",
            {
                "split_repairs": len(changes),
                "source_repairs": 1,
                "flagged_hadiths_retokenized": len(flagged_hadith_ids),
                **statuses,
                "external_reviews_relinked": review_links["relinked"],
            },
        )


if __name__ == "__main__":
    main()
