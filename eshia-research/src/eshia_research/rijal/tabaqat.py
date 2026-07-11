"""Phase C of the Tamyiz Engine: the tabaqat (generation) lattice.

Every narrator sits in a generation layer counted from the Prophet (0). A
chain is a strictly descending walk: the node nearer the compiler is one
generation later than the node it narrates from. Boroujerdi built the asanid
of al-Kafi by hand on exactly this principle; here it is automated as interval
constraint propagation.

Anchors:
* the 14 Ma'sumin at fixed layers (Prophet 0 ... al-Askari 10, al-Mahdi 11);
* Imam-companionship statements already parsed into
  `rijal_statements` (statement_type='tabaqah_membership', 4,117 rows) — a
  companion of an Imam at layer G is placed at layer G+1.

Propagation: for every *confident* resolved edge student->teacher (adjacent
resolved person mentions in a chain), gen(student) = gen(teacher) + 1. Intervals
are relaxed to a fixpoint; a contradiction widens to a `conflict` record rather
than crashing, so bad edges are surfaced, not hidden.

Output: one `person_generations` row per constrained person. Persons with no
anchor and no confident edge get no row — unknown generation stays unknown.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from eshia_research.corpus import CANONICAL_FOUR_BOOK_SOURCE_IDS
from eshia_research.models import (
    Book,
    Chain,
    ChainNode,
    Hadith,
    MentionResolution,
    Person,
    PersonGeneration,
    RijalStatement,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION

TABAQAT_VERSION = "tabaqat_c1"
GEN_MIN = 0
GEN_MAX = 15  # al-Kulayni (d. 329) sits around 11-12; headroom above.
MAX_ITERATIONS = 30

ProgressCallback = Callable[[str, int, int], None]


def _n(text: str) -> str:
    return normalise_arabic_persian(text)


# Fixed Imam layers, keyed by the Ma'sum person canonical_name_norm created in
# Phase A (person_builder.MASUMIN).
MASUM_GENERATIONS: dict[str, int] = {
    _n("النبي محمد صلى الله عليه وآله"): 0,
    _n("فاطمة الزهراء عليها السلام"): 1,
    _n("علي بن أبي طالب أمير المؤمنين عليه السلام"): 1,
    _n("الحسن بن علي المجتبى عليه السلام"): 2,
    _n("الحسين بن علي سيد الشهداء عليه السلام"): 2,
    _n("علي بن الحسين زين العابدين عليه السلام"): 3,
    _n("محمد بن علي الباقر عليه السلام"): 4,
    _n("جعفر بن محمد الصادق عليه السلام"): 5,
    _n("موسى بن جعفر الكاظم عليه السلام"): 6,
    _n("علي بن موسى الرضا عليه السلام"): 7,
    _n("محمد بن علي الجواد عليه السلام"): 8,
    _n("علي بن محمد الهادي عليه السلام"): 9,
    _n("الحسن بن علي العسكري عليه السلام"): 10,
    _n("الحجة المهدي عجل الله فرجه"): 11,
}

# imam_raw (from tabaqah_membership metadata) -> Imam layer, matched by keyword
# in specificity order so «الحسن العسكري» resolves before bare «الحسن».
_IMAM_KEYWORDS: tuple[tuple[str, int], ...] = (
    (_n("العسكري"), 10),
    (_n("ابي محمد"), 10),
    (_n("الهادي"), 9),
    (_n("الجواد"), 8),
    (_n("الرضا"), 7),
    (_n("الكاظم"), 6),
    (_n("الصادق"), 5),
    (_n("الباقر"), 4),
    (_n("السجاد"), 3),
    (_n("زين العابدين"), 3),
    (_n("علي بن الحسين"), 3),
    (_n("الحسين"), 2),
    (_n("الحسن"), 2),
    (_n("امير المؤمنين"), 1),
    (_n("علي"), 1),
    (_n("رسول"), 0),
    (_n("النبي"), 0),
    (_n("الرسول"), 0),
)


# «أبي الحسن» is a kunya shared by al-Kazim (6), al-Rida (7) and al-Hadi (9). On
# its own it does not identify an Imam, and must NOT fall through to the bare
# «الحسن» -> layer 2 keyword (which would be wrong). It only disambiguates when a
# more specific honorific accompanies it.
_ABU_AL_HASAN = _n("ابي الحسن")
_ABU_AL_HASAN_DISAMBIGUATORS = tuple(
    _n(k) for k in ("العسكري", "ابي محمد", "الهادي", "الرضا", "الكاظم")
)


def imam_generation_from_raw(imam_raw: str | None) -> int | None:
    if not imam_raw:
        return None
    norm = _n(imam_raw)
    if _ABU_AL_HASAN in norm and not any(k in norm for k in _ABU_AL_HASAN_DISAMBIGUATORS):
        # Ambiguous kunya with no disambiguator -> unanchorable, not layer 2.
        return None
    for keyword, generation in _IMAM_KEYWORDS:
        if keyword in norm:
            return generation
    return None


class Interval:
    __slots__ = ("lo", "hi")

    def __init__(self, lo: int, hi: int):
        self.lo = lo
        self.hi = hi

    def tighten(self, lo: int, hi: int) -> bool:
        """Intersect with [lo, hi]; return True if it changed. Never inverts —
        a would-be-empty intersection is refused (the caller flags conflict)."""
        new_lo = max(self.lo, lo)
        new_hi = min(self.hi, hi)
        if new_lo > new_hi:
            return False
        if new_lo == self.lo and new_hi == self.hi:
            return False
        self.lo, self.hi = new_lo, new_hi
        return True

    def would_conflict(self, lo: int, hi: int) -> bool:
        return max(self.lo, lo) > min(self.hi, hi)


def build_tabaqat(
    db: Session,
    *,
    source_book_ids=None,
    book_ids=None,
    on_progress: ProgressCallback | None = None,
    commit: bool = True,
) -> dict[str, int]:
    def progress(phase: str, done: int, total: int) -> None:
        if on_progress is not None:
            on_progress(phase, done, total)

    db.execute(delete(PersonGeneration))
    db.flush()

    intervals: dict[int, Interval] = {}
    method: dict[int, str] = {}
    evidence: dict[int, list[str]] = defaultdict(list)
    anchored: set[int] = set()

    # 1. Fixed Imam layers.
    person_rows = db.execute(
        select(Person.id, Person.canonical_name_norm, Person.canonical_name_ar, Person.kind)
    ).all()
    name_to_pid: dict[str, int] = {}
    for pid, name_norm, name_ar, kind in person_rows:
        name_to_pid.setdefault(name_norm, pid)
        gen = MASUM_GENERATIONS.get(name_norm)
        if gen is not None:
            intervals[pid] = Interval(gen, gen)
            method[pid] = "imam_fixed"
            anchored.add(pid)
            evidence[pid].append(f"Fixed Imam layer {gen}.")

    # 2. Imam-companionship anchors. A companion of an Imam at layer G narrates
    #    from him, so sits at layer G+1 (soft width +/-1).
    imam_layers_by_person: dict[int, list[int]] = defaultdict(list)
    stmt_rows = db.execute(
        select(RijalStatement.entry_id, RijalStatement.metadata_json)
        .where(RijalStatement.statement_type == "tabaqah_membership")
    ).all()
    entry_to_pid = {}
    for pid, entry_id in db.execute(
        select(Person.id, Person.primary_entry_id).where(Person.primary_entry_id.isnot(None))
    ):
        entry_to_pid[entry_id] = pid
    for entry_id, meta in stmt_rows:
        pid = entry_to_pid.get(entry_id)
        if pid is None or pid in anchored and method.get(pid) == "imam_fixed":
            continue
        imam_raw = (meta or {}).get("imam_raw") if isinstance(meta, dict) else None
        gen = imam_generation_from_raw(imam_raw)
        if gen is not None:
            imam_layers_by_person[pid].append(gen)

    for pid, layers in imam_layers_by_person.items():
        lo = min(layers) + 1 - 1
        hi = max(layers) + 1 + 1
        intervals[pid] = Interval(max(GEN_MIN, lo), min(GEN_MAX, hi))
        method[pid] = "ashab_anchor"
        anchored.add(pid)
        imams = ", ".join(str(g) for g in sorted(set(layers)))
        evidence[pid].append(f"Companion of Imam layer(s) {{{imams}}} -> generation ~{min(layers)+1}.")

    stats_anchors = len(anchored)

    # 3. Confident edges from resolved adjacent person mentions.
    selected_book_ids = _select_book_ids(db, source_book_ids, book_ids)
    edges: set[tuple[int, int]] = set()  # (student_pid, teacher_pid)
    edge_evidence: dict[tuple[int, int], int] = defaultdict(int)
    if selected_book_ids:
        resolved_by_node = _resolved_person_by_node(db, selected_book_ids)
        chain_positions = _chain_position_persons(db, selected_book_ids, resolved_by_node)
        for positions in chain_positions:
            # positions: sorted list of (position, person_id)
            for (p1, s), (p2, t) in zip(positions, positions[1:]):
                if p2 == p1 + 1 and s != t:
                    edges.add((s, t))
                    edge_evidence[(s, t)] += 1

    # Give every edge endpoint a starting interval if unconstrained.
    for s, t in edges:
        intervals.setdefault(s, Interval(GEN_MIN, GEN_MAX))
        intervals.setdefault(t, Interval(GEN_MIN, GEN_MAX))

    # 4. Relaxation to a fixpoint.
    conflicts: set[int] = set()
    for iteration in range(MAX_ITERATIONS):
        changed = False
        for s, t in edges:
            si, ti = intervals[s], intervals[t]
            # gen(student) = gen(teacher) + 1
            if si.would_conflict(ti.lo + 1, ti.hi + 1):
                # Only flag a real contradiction when the edge is corroborated
                # (seen in >= 2 chains); a lone edge is likely a misresolution
                # on one side, not a generation conflict for both persons.
                if edge_evidence[(s, t)] >= 2:
                    conflicts.add(s)
                    conflicts.add(t)
                continue
            if si.tighten(ti.lo + 1, ti.hi + 1):
                changed = True
            if ti.tighten(si.lo - 1, si.hi - 1):
                changed = True
        progress("relax", iteration + 1, MAX_ITERATIONS)
        if not changed:
            break

    # 5. Persist. Only persons with an anchor or a confident edge get a row.
    edge_persons = {p for edge in edges for p in edge}
    rows: list[dict] = []
    propagated = 0
    for pid, iv in intervals.items():
        is_anchor = pid in anchored
        has_edge = pid in edge_persons
        if not is_anchor and not has_edge:
            continue
        if pid in conflicts:
            m = "conflict"
        elif is_anchor and has_edge:
            m = "anchor_and_propagated"
        elif is_anchor:
            m = method.get(pid, "ashab_anchor")
        else:
            m = "propagated"
            propagated += 1
        point = iv.lo if iv.lo == iv.hi else (iv.lo if is_anchor else (iv.lo + iv.hi) // 2)
        summ = " ".join(evidence.get(pid, [])) or (
            f"Propagated from {edge_evidence and ''}transmission edges to [{iv.lo}, {iv.hi}]."
        )
        rows.append({
            "person_id": pid,
            "gen_lo": iv.lo,
            "gen_hi": iv.hi,
            "gen_point": point,
            "method": m,
            "evidence_summary": summ[:1000],
            "evidence_json": {"lo": iv.lo, "hi": iv.hi, "anchor": is_anchor, "edges": has_edge},
            "resolver_version": TABAQAT_VERSION,
        })

    db.bulk_insert_mappings(PersonGeneration, rows)
    if commit:
        db.commit()

    return {
        "persons_constrained": len(rows),
        "imam_fixed": sum(1 for r in rows if r["method"] == "imam_fixed"),
        "ashab_anchors": stats_anchors - sum(1 for r in rows if r["method"] == "imam_fixed"),
        "propagated_only": propagated,
        "conflicts": len(conflicts),
        "edges": len(edges),
        "tight_points": sum(1 for r in rows if r["gen_lo"] == r["gen_hi"]),
    }


def refine_with_tabaqat(
    db: Session,
    *,
    source_book_ids=None,
    book_ids=None,
    tolerance: int = 1,
    on_progress: ProgressCallback | None = None,
    commit: bool = True,
) -> dict[str, int]:
    """Disambiguate ambiguous mentions using generation constraints.

    For an ambiguous imam or narrator node whose candidates all have a known
    generation, the nearest resolved neighbour with a known generation fixes
    the expected layer (each chain step is one layer): gen(node) =
    gen(neighbour) - (node_pos - neighbour_pos). If exactly one candidate lands
    within `tolerance` of that expected layer, the node is upgraded to
    ``resolved`` with a tabaqa dalil; its previous ambiguous rows are replaced.

    This is the mechanism that turns «أبو جعفر ع» into al-Baqir (layer 4) vs
    al-Jawad (layer 8) from the surrounding narrators. Conservative: candidates
    with unknown generation are never pruned, so nodes stay honestly ambiguous
    unless the evidence is decisive.
    """
    from eshia_research.models import Person as _Person

    selected_book_ids = _select_book_ids(db, source_book_ids, book_ids)
    stats = {"imam_disambiguated": 0, "narrator_disambiguated": 0, "nodes_examined": 0}
    if not selected_book_ids:
        return stats

    gen_point: dict[int, int] = {
        pid: pt
        for pid, pt in db.execute(
            select(PersonGeneration.person_id, PersonGeneration.gen_point)
            .where(
                PersonGeneration.gen_point.isnot(None),
                # A person whose own generation evidence is self-contradictory
                # must not anchor or disambiguate other narrators' identities.
                PersonGeneration.method != "conflict",
            )
        )
    }
    person_name_ar: dict[int, str] = {
        pid: name for pid, name in db.execute(select(_Person.id, _Person.canonical_name_ar))
    }

    chains = db.execute(
        select(Chain.id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .where(Hadith.book_id.in_(selected_book_ids))
        .order_by(Chain.id)
    ).scalars().all()

    total = len(chains)
    for done, chain_id in enumerate(chains, start=1):
        nodes = db.execute(
            select(ChainNode.id, ChainNode.position, ChainNode.node_type)
            .where(ChainNode.chain_id == chain_id)
            .order_by(ChainNode.position)
        ).all()
        # Current resolutions per node.
        node_res: dict[int, list[MentionResolution]] = {}
        for node_id, _, _ in nodes:
            node_res[node_id] = db.execute(
                select(MentionResolution)
                .where(
                    MentionResolution.chain_node_id == node_id,
                    MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
                )
                .order_by(MentionResolution.rank)
            ).scalars().all()

        # Anchor generations from currently-resolved single-person nodes.
        anchor_gen: dict[int, int] = {}  # position -> generation
        for node_id, position, _ in nodes:
            rows = node_res[node_id]
            if len(rows) == 1 and rows[0].status in ("resolved", "via_collective") and rows[0].person_id in gen_point:
                anchor_gen[position] = gen_point[rows[0].person_id]

        if not anchor_gen:
            if on_progress and done % 1000 == 0:
                on_progress("refine", done, total)
            continue

        for node_id, position, node_type in nodes:
            rows = node_res[node_id]
            if len(rows) < 2 or any(r.status not in ("ambiguous",) for r in rows):
                continue
            stats["nodes_examined"] += 1
            candidate_pids = [r.person_id for r in rows if r.person_id is not None]
            cand_gens = {pid: gen_point.get(pid) for pid in candidate_pids}
            if any(g is None for g in cand_gens.values()):
                # Some candidate has unknown generation — cannot safely prune.
                continue
            # Nearest anchor by chain distance.
            nearest = min(anchor_gen, key=lambda pr: abs(position - pr))
            expected = anchor_gen[nearest] - (position - nearest)
            survivors = [pid for pid in candidate_pids if abs(cand_gens[pid] - expected) <= tolerance]
            if len(survivors) != 1:
                continue
            winner = survivors[0]
            # Replace this node's resolutions with a single tabaqa-resolved row.
            for r in rows:
                db.delete(r)
            db.flush()
            db.add(MentionResolution(
                chain_node_id=node_id,
                person_id=winner,
                rank=1,
                status="resolved",
                method="tabaqat_disambiguated",
                evidence_summary=(
                    f"Generation {gen_point[winner]} fits the chain: expected ~{expected} "
                    f"from {person_name_ar.get(_anchor_person(node_res, nodes, nearest))} "
                    f"(gen {anchor_gen[nearest]}, {abs(position - nearest)} step(s) away). "
                    f"Chosen {person_name_ar.get(winner)} over "
                    f"{len(candidate_pids) - 1} generation-incompatible candidate(s)."
                ),
                evidence_json={"expected_gen": expected, "winner_gen": gen_point[winner],
                               "anchor_position": nearest, "tolerance": tolerance},
                resolver_version=PERSON_RESOLVER_VERSION,
            ))
            if node_type == "imam":
                stats["imam_disambiguated"] += 1
            else:
                stats["narrator_disambiguated"] += 1
        if on_progress and done % 1000 == 0:
            on_progress("refine", done, total)

    if commit:
        db.commit()
    return stats


def _anchor_person(node_res, nodes, position: int) -> int | None:
    for node_id, pos, _ in nodes:
        if pos == position:
            rows = node_res.get(node_id, [])
            if rows:
                return rows[0].person_id
    return None


def _select_book_ids(db: Session, source_book_ids, book_ids) -> list[int]:
    query = db.query(Book.id)
    if book_ids:
        query = query.filter(Book.id.in_(book_ids))
    else:
        selected = tuple(source_book_ids or CANONICAL_FOUR_BOOK_SOURCE_IDS)
        query = query.filter(Book.source_book_id.in_(selected))
    return [row[0] for row in query.all()]


def _resolved_person_by_node(db: Session, book_ids: list[int]) -> dict[int, int]:
    """chain_node_id -> person_id for uniquely resolved mentions only."""
    rows = db.execute(
        select(MentionResolution.chain_node_id, MentionResolution.person_id)
        .join(ChainNode, ChainNode.id == MentionResolution.chain_node_id)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .where(
            Hadith.book_id.in_(book_ids),
            MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
            MentionResolution.status == "resolved",
            MentionResolution.person_id.isnot(None),
        )
    ).all()
    return {node_id: pid for node_id, pid in rows}


def _chain_position_persons(
    db: Session, book_ids: list[int], resolved_by_node: dict[int, int]
) -> list[list[tuple[int, int]]]:
    """Per chain, the sorted (position, person_id) of its resolved nodes."""
    rows = db.execute(
        select(ChainNode.chain_id, ChainNode.position, ChainNode.id)
        .join(Chain, Chain.id == ChainNode.chain_id)
        .join(Hadith, Hadith.id == Chain.hadith_id)
        .where(Hadith.book_id.in_(book_ids))
        .order_by(ChainNode.chain_id, ChainNode.position)
    ).all()
    by_chain: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for chain_id, position, node_id in rows:
        pid = resolved_by_node.get(node_id)
        if pid is not None:
            by_chain[chain_id].append((position, pid))
    return list(by_chain.values())
