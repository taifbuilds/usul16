"""Phase B of the Tamyiz Engine: the reference calculus.

Resolves chain-node MENTIONS to PERSONS (Phase A's `persons`), writing
`mention_resolutions` rows — a claim separate from the entry-level
`chain_nodes.canonical_narrator_id`. This layer is deliberately deterministic:
it does the reasoning a reader does before any statistical disambiguation.

What it resolves, per node, always with a dalil (evidence dossier):

* named narrator / imam — surface-form lookup against the person layer;
  a bare form claimed by many persons stays honestly ``ambiguous`` with the
  full ranked candidate set (Phase D narrows it), a unique form resolves;
* «عن أبيه» / «عن جده» — the father/grandfather of the *previous* mention,
  found first via a documented `person_relations` edge, else via the
  nasab-asserted father name (for فلان بن X the father IS X); when no person
  matches, a ``latent`` person is minted so the graph stays connected and the
  gap is visible rather than dropped;
* «عنه» (anaphora) — the opening narrator of the previous chain in the hadith;
* «عدة من أصحابنا منهم فلان» and documented 'iddah rosters — the named member(s)
  are resolved and attributed ``via_collective``, never as direct transmission.

Nothing here edits chain text or the Phase A tables; it only (re)builds
`mention_resolutions` for the selected books.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from eshia_research.corpus import CANONICAL_FOUR_BOOK_SOURCE_IDS
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    CollectiveRoster,
    Hadith,
    MentionResolution,
    Person,
    PersonRelation,
    PersonSurfaceForm,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.name_grammar import parse_name

PERSON_RESOLVER_VERSION = "tamyiz_b1"
MAX_CANDIDATES = 6
MAX_MEMBER_WINDOW = 6

REJECTED_HADITH_STATUS = "rejected_non_hadith_fragment"

ProgressCallback = Callable[[str, int, int], None]

_BARE_JOIN = f" {normalise_arabic_persian('بن')} "
_WAW = normalise_arabic_persian("و")
_MINHUM = normalise_arabic_persian("منهم")
_KULLUHUM = {normalise_arabic_persian(w) for w in ("کلهم", "جمیعا", "جميعا", "کلها")}
_ABU_VARIANTS = tuple(normalise_arabic_persian(w) for w in ("ابو", "ابی", "ابا"))
_COMPOUND_HEADS = {normalise_arabic_persian(w) for w in ("عبد", "عبید")}
# Leading connector strip for member fragments.
_LEAD_CONNECTOR_RE = re.compile(rf"^(?:{_WAW}\s*|،\s*|؛\s*)+")


def _n(text: str) -> str:
    return normalise_arabic_persian(text)


def _token_case_variants(norm: str) -> list[str]:
    """Kunya case alternation (ابو/ابی/ابا) + internal ابن/بن drift."""
    variants = [norm]
    for head in _ABU_VARIANTS:
        if norm.startswith(head + " "):
            rest = norm[len(head) + 1 :]
            variants.extend(f"{v} {rest}" for v in _ABU_VARIANTS)
            break
    ibn = _n("ابن")
    bin_ = _n("بن")
    if f" {ibn} " in norm:
        variants.append(norm.replace(f" {ibn} ", f" {bin_} "))
    out: list[str] = []
    seen: set[str] = set()
    for v in variants:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


@dataclass
class PersonLookup:
    # form_norm -> list of (person_id, derivation, shared_count)
    form_index: dict[str, list[tuple[int, str, int]]]
    person_kind: dict[int, str]
    person_name: dict[int, str]
    person_name_ar: dict[int, str]
    # person_id -> (related_person_id | None, related_name_norm | None)
    father_of: dict[int, tuple[int | None, str | None]]
    # keyed_by_norm -> list of (member_name_ar, member_name_norm, member_person_id, citation, confidence)
    rosters: dict[str, list[tuple[str, str, int | None, str, int]]]

    def candidates_for(self, token_norm: str) -> tuple[list[tuple[int, str, int]], str | None]:
        """Return (ranked person candidates, matched_form) for a token.

        Candidates are (person_id, derivation, shared_count). A more specific
        derivation (full > truncation > first_name/kunya/ibn/nisba) wins the
        ranking; shared_count breaks ties (rarer form = stronger signal).
        bare_form_proxy persons are excluded — they are evidence documents,
        not identities, so a bare mention surfaces its real claimants instead.
        """
        # Query forms, most specific first: exact token variants, then — if
        # nothing hits — the bare nasab from parsing the token, so a chain
        # token carrying a kunya prefix or trailing words («ابو جعفر محمد بن
        # یعقوب») still finds «محمد بن یعقوب». No further truncation: that
        # would throw away specificity the token actually has.
        query_forms = list(_token_case_variants(token_norm))
        parsed = parse_name(token_norm)
        if parsed.units and not parsed.is_ibn_form:
            bare_nasab = _BARE_JOIN.join(parsed.units)
            if parsed.nisba_parts:
                bare_nasab = f"{bare_nasab} {parsed.nisba_parts[0]}"
            for variant in _token_case_variants(bare_nasab):
                if variant not in query_forms:
                    query_forms.append(variant)

        best_form: str | None = None
        hits: dict[int, tuple[int, str, int]] = {}
        for variant in query_forms:
            entries = self.form_index.get(variant)
            if not entries:
                continue
            if best_form is None:
                best_form = variant
            for person_id, derivation, shared in entries:
                if self.person_kind.get(person_id) == "bare_form_proxy":
                    continue
                rank_key = _DERIVATION_RANK.get(derivation, 9)
                current = hits.get(person_id)
                if current is None or rank_key < _DERIVATION_RANK.get(current[1], 9):
                    hits[person_id] = (person_id, derivation, shared)
            if hits:
                # Stop at the first query form that matched — mixing exact and
                # parsed-fallback hits would conflate specificity tiers.
                break
        ranked = sorted(
            hits.values(),
            key=lambda c: (_DERIVATION_RANK.get(c[1], 9), c[2], c[0]),
        )
        return ranked[:MAX_CANDIDATES], best_form

    def decisive(
        self, ranked: list[tuple[int, str, int]], matched_form: str | None = None
    ) -> int | None:
        """The single person if the best derivation tier has one clear winner.

        «محمد بن یحیی العطار» matches one person as a `full` form and others
        only as a `nasab_truncation`; the full match is decisive. When several
        share the best tier, an exact canonical-title match breaks the tie
        («محمد بن يحيى العطار» beats the nisba-less form of «محمد بن يحيى أبو
        جعفر العطار»). A bare «أحمد بن محمد» matches everyone at the same tier
        with no exact title — stays ambiguous.
        """
        if not ranked:
            return None
        best_rank = _DERIVATION_RANK.get(ranked[0][1], 9)
        top = [c for c in ranked if _DERIVATION_RANK.get(c[1], 9) == best_rank]
        if len(top) == 1:
            return top[0][0]
        if matched_form:
            exact = [c for c in top if self.person_name.get(c[0]) == matched_form]
            if len(exact) == 1:
                return exact[0][0]
        return None


_DERIVATION_RANK = {
    "full": 0,
    "masum_title": 0,
    "entry_title": 1,
    "nasab_truncation": 2,
    "ibn_form": 3,
    "nisba_form": 4,
    "kunya": 5,
    "first_name": 6,
}


def build_person_lookup(db: Session) -> PersonLookup:
    form_index: dict[str, list[tuple[int, str, int]]] = defaultdict(list)
    for person_id, form_norm, derivation, shared in db.execute(
        select(
            PersonSurfaceForm.person_id,
            PersonSurfaceForm.form_norm,
            PersonSurfaceForm.derivation,
            PersonSurfaceForm.shared_count,
        )
    ):
        form_index[form_norm].append((person_id, derivation, shared))

    person_kind: dict[int, str] = {}
    person_name: dict[int, str] = {}
    person_name_ar: dict[int, str] = {}
    for pid, kind, name_norm, name_ar in db.execute(
        select(Person.id, Person.kind, Person.canonical_name_norm, Person.canonical_name_ar)
    ):
        person_kind[pid] = kind
        person_name[pid] = name_norm
        person_name_ar[pid] = name_ar

    father_of: dict[int, tuple[int | None, str | None]] = {}
    for pid, related_pid, related_norm in db.execute(
        select(
            PersonRelation.person_id,
            PersonRelation.related_person_id,
            PersonRelation.related_name_norm,
        ).where(PersonRelation.relation_kind == "father")
    ):
        # Prefer a matched relation if several rows exist for one person.
        if pid not in father_of or (related_pid is not None and father_of[pid][0] is None):
            father_of[pid] = (related_pid, related_norm)

    rosters: dict[str, list[tuple[str, str, int | None, str, int]]] = defaultdict(list)
    for keyed, m_ar, m_norm, m_pid, citation, conf in db.execute(
        select(
            CollectiveRoster.keyed_by_norm,
            CollectiveRoster.member_name_ar,
            CollectiveRoster.member_name_norm,
            CollectiveRoster.member_person_id,
            CollectiveRoster.source_citation,
            CollectiveRoster.confidence,
        )
    ):
        rosters[keyed].append((m_ar, m_norm, m_pid, citation, conf))

    return PersonLookup(
        form_index=dict(form_index),
        person_kind=person_kind,
        person_name=person_name,
        person_name_ar=person_name_ar,
        father_of=dict(father_of),
        rosters=dict(rosters),
    )


# A waw that begins the next member: «...العطار والحسن...». Split it when the
# waw is immediately followed by a common name-start (ال / kunya / compound /
# ابن), which covers the overwhelming majority of roster names without
# breaking genuinely waw-initial isms like «وهب».
_MEMBER_NAME_STARTS = (_n("ال"), _n("ابو"), _n("ابی"), _n("ابا"), _n("ابن"), _n("عبد"), _n("عبید"))
_WAW_SPLIT_RE = re.compile(rf"(?:^|\s)و(?={'|'.join(re.escape(s) for s in _MEMBER_NAME_STARTS)})")


def _member_fragments(tail: str) -> list[str]:
    tail = _WAW_SPLIT_RE.sub(" | ", tail)
    tail = tail.replace(f" {_WAW} ", " | ").replace("،", " | ").replace("؛", " | ")
    return [frag.strip() for frag in tail.split("|") if frag.strip()]


def split_collective_members(token_norm: str, lookup: PersonLookup) -> list[tuple[str, int | None]]:
    """Extract explicitly named members from «... منهم X و Y و Z [کلهم]».

    Splits the member list on waw/comma boundaries, then greedy longest-matches
    each fragment against the surface-form index (so multi-token names and
    kunyas stay intact). Returns (member_norm, person_id | None) — an
    unmatched or ambiguous fragment is kept name-only rather than guessed.
    """
    idx = token_norm.find(_MINHUM)
    if idx == -1:
        return []
    tail = _LEAD_CONNECTOR_RE.sub("", token_norm[idx + len(_MINHUM) :].strip())

    members: list[tuple[str, int | None]] = []
    for fragment in _member_fragments(tail):
        tokens = [t for t in fragment.split() if t and t not in _KULLUHUM]
        i, n = 0, len(tokens)
        while i < n:
            matched: tuple[int, int | None] | None = None
            for j in range(min(n, i + MAX_MEMBER_WINDOW), i, -1):
                window = " ".join(tokens[i:j]).strip()
                if not window:
                    continue
                cands, matched_form = lookup.candidates_for(window)
                decisive_pid = lookup.decisive(cands, matched_form)
                if decisive_pid is not None:
                    matched = (j, decisive_pid)
                    members.append((window, decisive_pid))
                    break
                if cands and matched is None:
                    matched = (j, None)
            if matched is not None:
                if matched[1] is None:
                    window = " ".join(tokens[i : matched[0]]).strip()
                    members.append((window, None))
                i = matched[0]
            else:
                i += 1
    return members


@dataclass
class PersonResolutionStats:
    nodes_seen: int = 0
    resolved: int = 0
    ambiguous: int = 0
    via_collective: int = 0
    latent_minted: int = 0
    unresolved: int = 0
    father_resolved: int = 0
    anaphora_resolved: int = 0
    collective_members: int = 0
    resolution_rows: int = 0
    method_counts: Counter = field(default_factory=Counter)


def _select_book_ids(db: Session, source_book_ids, book_ids) -> list[int]:
    query = db.query(Book.id)
    if book_ids:
        query = query.filter(Book.id.in_(book_ids))
    else:
        selected = tuple(source_book_ids or CANONICAL_FOUR_BOOK_SOURCE_IDS)
        query = query.filter(Book.source_book_id.in_(selected))
    return [row[0] for row in query.all()]


def rebuild_person_resolutions(
    db: Session,
    *,
    source_book_ids=None,
    book_ids=None,
    on_progress: ProgressCallback | None = None,
    commit: bool = True,
) -> PersonResolutionStats:
    stats = PersonResolutionStats()
    selected_book_ids = _select_book_ids(db, source_book_ids, book_ids)
    if not selected_book_ids:
        return stats

    lookup = build_person_lookup(db)

    # Clear this resolver version's rows for the selected books.
    hadith_ids_subq = select(Hadith.id).where(Hadith.book_id.in_(selected_book_ids))
    chain_ids_subq = select(Chain.id).where(Chain.hadith_id.in_(hadith_ids_subq))
    node_ids_subq = select(ChainNode.id).where(ChainNode.chain_id.in_(chain_ids_subq))
    db.execute(
        delete(MentionResolution).where(
            MentionResolution.chain_node_id.in_(node_ids_subq),
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
        )
    )
    db.flush()

    chains = (
        db.query(Chain.id, Chain.hadith_id)
        .join(Hadith, Chain.hadith_id == Hadith.id)
        .filter(
            Hadith.book_id.in_(selected_book_ids),
            Hadith.review_status != REJECTED_HADITH_STATUS,
        )
        .order_by(Hadith.id, Chain.chain_number)
        .all()
    )

    # Opening person of each chain, for «عنه» anaphora to the previous chain.
    opening_person_by_chain: dict[int, int | None] = {}
    prev_chain_in_hadith: dict[int, int | None] = {}
    last_chain_for_hadith: dict[int, int] = {}
    for chain_id, hadith_id in chains:
        prev_chain_in_hadith[chain_id] = last_chain_for_hadith.get(hadith_id)
        last_chain_for_hadith[hadith_id] = chain_id

    total = len(chains)
    minted_names: dict[str, int] = {}  # latent person cache within this run
    pending_persons: list[dict] = []
    next_latent_id = (db.query(Person.id).order_by(Person.id.desc()).first() or (0,))[0] + 1

    def emit(node_id, person_id, rank, status, method, summary, evidence):
        stats.resolution_rows += 1
        stats.method_counts[method] += 1
        db.add(
            MentionResolution(
                chain_node_id=node_id,
                person_id=person_id,
                rank=rank,
                status=status,
                method=method,
                evidence_summary=summary,
                evidence_json=evidence,
                resolver_version=PERSON_RESOLVER_VERSION,
            )
        )

    for done, (chain_id, hadith_id) in enumerate(chains, start=1):
        nodes = (
            db.query(ChainNode)
            .filter(ChainNode.chain_id == chain_id)
            .order_by(ChainNode.position)
            .all()
        )
        prev_person: int | None = None  # resolved person of the previous mention
        prev_token_norm: str | None = None  # its token, for nasab-derived kinship
        for pos, node in enumerate(nodes):
            stats.nodes_seen += 1
            node_type = node.node_type
            relation = node.relation_kind

            if node_type in ("named_narrator", "imam"):
                cands, matched_form = lookup.candidates_for(node.token_normalised)
                prev_token_norm = node.token_normalised
                decisive_pid = lookup.decisive(cands, matched_form)
                if not cands:
                    stats.unresolved += 1
                    emit(node.id, None, 1, "unresolved", "no_surface_form",
                         f"No person surface form matches «{node.token_normalised}».", None)
                    prev_person = None
                elif decisive_pid is not None:
                    derivation = next(d for p, d, _ in cands if p == decisive_pid)
                    shared = next(s for p, _, s in cands if p == decisive_pid)
                    stats.resolved += 1
                    summary = (
                        f"Decisive person for «{matched_form}» "
                        f"({derivation}, sole match at that specificity): "
                        f"{lookup.person_name_ar.get(decisive_pid)}."
                    )
                    emit(node.id, decisive_pid, 1, "resolved", f"surface_{derivation}", summary,
                         {"matched_form": matched_form, "derivation": derivation, "shared_count": shared})
                    prev_person = decisive_pid
                else:
                    stats.ambiguous += 1
                    for rank, (pid, derivation, shared) in enumerate(cands, start=1):
                        summary = (
                            f"«{matched_form}» ({derivation}) is shared by {shared} persons; "
                            f"candidate {rank}: {lookup.person_name_ar.get(pid)}."
                        )
                        emit(node.id, pid, rank, "ambiguous", f"surface_{derivation}", summary,
                             {"matched_form": matched_form, "derivation": derivation,
                              "shared_count": shared, "candidate_count": len(cands)})
                    prev_person = None  # too ambiguous to anchor a father reference

            elif node_type == "pronoun_relation" and relation in ("father", "grandfather"):
                resolved = _resolve_kin(node, relation, prev_person, prev_token_norm, lookup)
                father_name = _asserted_kin_name(prev_person, prev_token_norm, relation, lookup)
                cands = lookup.candidates_for(father_name)[0] if father_name else []
                if resolved is not None:
                    # Unique / documented kin match.
                    pid, method, summary, evidence, matched = resolved
                    stats.father_resolved += 1
                    stats.resolved += 1
                    emit(node.id, pid, 1, "resolved", method, summary, evidence)
                    prev_person = pid
                    prev_token_norm = matched
                elif len(cands) > 1:
                    # The father is named by the nasab but shared by several
                    # persons — show them, do NOT invent a person.
                    stats.ambiguous += 1
                    for rank, (pid, derivation, shared) in enumerate(cands, start=1):
                        emit(node.id, pid, rank, "ambiguous", f"{relation}_nasab_ambiguous",
                             f"«{node.token_normalised}» = {relation} named «{father_name}»; "
                             f"shared by {shared} persons, candidate {rank}: "
                             f"{lookup.person_name_ar.get(pid)}.",
                             {"asserted_name": father_name, "candidate_count": len(cands)})
                    prev_person = None
                    prev_token_norm = father_name
                elif father_name:
                    # Named by the nasab but no Mu'jam person at all — mint a
                    # latent person so the graph stays connected and visible.
                    key = f"latent::{father_name}"
                    if key in minted_names:
                        pid = minted_names[key]
                    else:
                        pid = next_latent_id
                        next_latent_id += 1
                        minted_names[key] = pid
                        pending_persons.append({
                            "id": pid,
                            "canonical_name_ar": father_name,
                            "canonical_name_norm": father_name,
                            "kind": "latent",
                            "origin": "nasab_kinship",
                            "notes": f"minted as {relation} asserted by nasab, no Mu'jam entry matched",
                        })
                        stats.latent_minted += 1
                    stats.resolved += 1
                    emit(node.id, pid, 1, "latent", f"{relation}_latent_from_nasab",
                         f"«{node.token_normalised}» = {relation} of previous narrator, named "
                         f"«{father_name}» by the nasab; no Mu'jam person matched, minted latent.",
                         {"asserted_name": father_name, "relation": relation})
                    prev_person = pid
                    prev_token_norm = father_name
                else:
                    stats.unresolved += 1
                    emit(node.id, None, 1, "unresolved", f"{relation}_no_antecedent",
                         f"«{node.token_normalised}» has no resolvable antecedent to derive {relation}.",
                         None)
                    prev_person = None

            elif node_type == "pronoun_relation" and relation == "anaphora":
                prev_chain = prev_chain_in_hadith.get(chain_id)
                anchor = opening_person_by_chain.get(prev_chain) if prev_chain else None
                if anchor is not None:
                    stats.anaphora_resolved += 1
                    stats.resolved += 1
                    emit(node.id, anchor, 1, "resolved", "anaphora_previous_chain",
                         f"«{node.token_normalised}» refers to the opening narrator of the "
                         f"previous chain: {lookup.person_name_ar.get(anchor)}.",
                         {"previous_chain_id": prev_chain})
                    prev_person = anchor
                else:
                    stats.unresolved += 1
                    emit(node.id, None, 1, "unresolved", "anaphora_no_previous",
                         f"«{node.token_normalised}» anaphora with no resolvable previous chain opening.", None)
                    prev_person = None

            elif node_type == "collective_phrase":
                # Resolve embedded «منهم» members and any documented roster
                # keyed by the NEXT narrator (position pos+1).
                members = split_collective_members(node.token_normalised, lookup)
                next_person = _peek_next_person(nodes, pos, lookup)
                roster = lookup.rosters.get(lookup.person_name.get(next_person, "")) if next_person else None
                emitted_any = False
                rank = 1
                seen_members: set[int] = set()
                for member_norm, member_pid in members:
                    stats.collective_members += 1
                    if member_pid is not None and member_pid not in seen_members:
                        seen_members.add(member_pid)
                        stats.via_collective += 1
                        emitted_any = True
                        emit(node.id, member_pid, rank, "via_collective", "collective_named_member",
                             f"Named member of the collective «عدة/جماعة»: "
                             f"{lookup.person_name_ar.get(member_pid)}.",
                             {"member_form": member_norm})
                        rank += 1
                if roster:
                    for m_ar, m_norm, m_pid, citation, conf in roster:
                        if m_pid is not None and m_pid not in seen_members:
                            seen_members.add(m_pid)
                            stats.via_collective += 1
                            emitted_any = True
                            emit(node.id, m_pid, rank, "via_collective", "collective_roster_member",
                                 f"Documented 'iddah member (keyed by "
                                 f"{lookup.person_name_ar.get(next_person)}): {m_ar}. Source: {citation}.",
                                 {"roster_key": lookup.person_name.get(next_person), "citation": citation,
                                  "confidence": conf})
                            rank += 1
                if not emitted_any:
                    stats.unresolved += 1
                    emit(node.id, None, 1, "unresolved", "collective_unexpanded",
                         f"Collective «{node.token_normalised[:60]}» — no member resolved.", None)
                prev_person = None  # a collective does not anchor a single father

            else:
                stats.unresolved += 1
                emit(node.id, None, 1, "unresolved", "unhandled_node_type",
                     f"Node type {node_type} not handled by the reference calculus.", None)
                prev_person = None

            if pos == 0:
                opening_person_by_chain[chain_id] = prev_person

        if commit and done % 400 == 0:
            if pending_persons:
                db.bulk_insert_mappings(Person, pending_persons)
                pending_persons.clear()
            db.commit()
        if on_progress and (done % 500 == 0 or done == total):
            on_progress("resolve chains", done, total)

    if pending_persons:
        db.bulk_insert_mappings(Person, pending_persons)
    if commit:
        db.commit()
    return stats


def _peek_next_person(nodes: list[ChainNode], pos: int, lookup: PersonLookup) -> int | None:
    for node in nodes[pos + 1 :]:
        if node.node_type in ("named_narrator", "imam"):
            cands, _ = lookup.candidates_for(node.token_normalised)
            if len(cands) == 1:
                return cands[0][0]
            return None
    return None


def _asserted_kin_name(prev_person, prev_token_norm, relation, lookup) -> str | None:
    """The name the nasab asserts for the father of the previous mention.

    Prefers a documented `person_relations` father name; falls back to parsing
    the previous token itself (for «محمد بن سعد بن خلف» the father IS
    «سعد بن خلف»), so kinship works even when the previous narrator has no
    Mu'jam entry. Grandfather names are not asserted by a single token.
    """
    if relation != "father":
        return None
    if prev_person is not None:
        _, related_norm = lookup.father_of.get(prev_person, (None, None))
        if related_norm:
            return related_norm
    if prev_token_norm:
        parsed = parse_name(prev_token_norm)
        if not parsed.is_ibn_form:
            return parsed.father_norm
    return None


def _resolve_kin(node, relation, prev_person, prev_token_norm, lookup):
    """Resolve «أبيه»/«جده» to a documented person via the previous mention."""
    if relation == "father":
        # Documented father edge of a known antecedent person.
        if prev_person is not None:
            related_pid, related_norm = lookup.father_of.get(prev_person, (None, None))
            if related_pid is not None:
                return (
                    related_pid,
                    "father_relation_matched",
                    f"«{node.token_normalised}» = father of "
                    f"{lookup.person_name_ar.get(prev_person)}, documented as "
                    f"{lookup.person_name_ar.get(related_pid)}.",
                    {"antecedent_person": prev_person, "via": "person_relation"},
                    lookup.person_name.get(related_pid, related_norm),
                )
        # Otherwise, unique person for the nasab-asserted father name.
        father_name = _asserted_kin_name(prev_person, prev_token_norm, "father", lookup)
        if father_name:
            cands, _ = lookup.candidates_for(father_name)
            if len(cands) == 1:
                pid = cands[0][0]
                return (
                    pid,
                    "father_nasab_unique",
                    f"«{node.token_normalised}» = father named «{father_name}» by the nasab; "
                    f"unique person match: {lookup.person_name_ar.get(pid)}.",
                    {"asserted_name": father_name},
                    lookup.person_name.get(pid, father_name),
                )
        return None
    # grandfather: father of the father.
    if prev_person is not None:
        related_pid, _ = lookup.father_of.get(prev_person, (None, None))
        if related_pid is not None:
            gp_pid, gp_norm = lookup.father_of.get(related_pid, (None, None))
            if gp_pid is not None:
                return (
                    gp_pid,
                    "grandfather_two_step",
                    f"«{node.token_normalised}» = grandfather of "
                    f"{lookup.person_name_ar.get(prev_person)} via "
                    f"{lookup.person_name_ar.get(related_pid)}.",
                    {"antecedent_person": prev_person, "father_person": related_pid},
                    lookup.person_name.get(gp_pid, gp_norm),
                )
    return None
