"""Deterministic English-formula rendering for hadith chains."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload

from eshia_research.models import (
    Chain,
    ChainNode,
    Hadith,
    MentionResolution,
    Narrator,
    Person,
    RijalEntry,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.rijal.effective_resolution import apply_admin_decision, load_admin_decisions
from eshia_research.rijal.person_resolver import PERSON_RESOLVER_VERSION


_TRANSMISSION_PHRASES = {
    normalise_arabic_persian("عن"): "from",
    normalise_arabic_persian("حدثنا"): "narrated to us by",
    normalise_arabic_persian("حدثني"): "narrated to me by",
    normalise_arabic_persian("أخبرنا"): "reported to us by",
    normalise_arabic_persian("اخبرنا"): "reported to us by",
    normalise_arabic_persian("أخبرني"): "reported to me by",
    normalise_arabic_persian("قال"): "said",
    normalise_arabic_persian("رفعه"): "raising it to",
    normalise_arabic_persian("يرفعه"): "raising it to",
}

_NON_STANDARD_CHAIN_STATUSES = {"needs_review", "reviewed_complex", "reviewed_exception"}


@dataclass(frozen=True)
class RenderedChainNode:
    node_id: int
    position: int
    source_token: str
    rendered_name: str
    name_source: str
    phrase_en: str | None
    risk_flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RenderedChain:
    chain_id: int
    chain_number: int
    text: str
    review_status: str
    parser_flags: str | None
    nodes: list[RenderedChainNode]
    risk_flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IsnadRenderResult:
    hadith_id: int
    public_id: str
    text: str | None
    chains: list[RenderedChain]
    risk_flags: list[str] = field(default_factory=list)


def render_hadith_isnad(db: Session, hadith_id: int) -> IsnadRenderResult:
    hadith = db.get(Hadith, hadith_id)
    if hadith is None:
        raise ValueError(f"Hadith {hadith_id} not found")

    chains = (
        db.query(Chain)
        .options(selectinload(Chain.nodes).selectinload(ChainNode.narrator))
        .filter(Chain.hadith_id == hadith_id)
        .order_by(Chain.chain_number)
        .all()
    )
    if not chains:
        return IsnadRenderResult(
            hadith_id=hadith.id,
            public_id=hadith.public_id,
            text=None,
            chains=[],
            risk_flags=["no_chain_index"],
        )

    node_ids = [node.id for chain in chains for node in chain.nodes]
    rank1 = {
        row.chain_node_id: row
        for row in db.execute(
            select(MentionResolution).where(
                MentionResolution.chain_node_id.in_(node_ids),
                MentionResolution.rank == 1,
                MentionResolution.resolver_version == PERSON_RESOLVER_VERSION,
            )
        ).scalars()
    }
    decisions = load_admin_decisions(
        db, resolver_version=PERSON_RESOLVER_VERSION, chain_node_ids=node_ids
    )

    effective_person_ids: set[int] = set()
    effective_by_node: dict[int, tuple[int | None, str, str]] = {}
    for node_id in node_ids:
        row = rank1.get(node_id)
        eff = apply_admin_decision(
            row.status if row else None,
            row.person_id if row else None,
            decisions.get(node_id),
        )
        effective_by_node[node_id] = (eff.person_id, eff.status, eff.source)
        if eff.person_id is not None:
            effective_person_ids.add(eff.person_id)

    persons = {
        person.id: person
        for person in db.execute(select(Person).where(Person.id.in_(effective_person_ids))).scalars()
    } if effective_person_ids else {}

    narrator_en_by_entry: dict[int, str] = {}
    entry_ids = {p.primary_entry_id for p in persons.values() if p.primary_entry_id is not None}
    if entry_ids:
        narrator_en_by_entry = {
            entry_id: name_en
            for entry_id, name_en in db.execute(
                select(RijalEntry.id, Narrator.canonical_name_en)
                .join(Narrator, Narrator.id == RijalEntry.narrator_id)
                .where(
                    and_(
                        RijalEntry.id.in_(entry_ids),
                        Narrator.canonical_name_en.isnot(None),
                    )
                )
            )
        }

    rendered_chains: list[RenderedChain] = []
    all_flags: set[str] = set()
    for chain in chains:
        node_parts: list[str] = []
        rendered_nodes: list[RenderedChainNode] = []
        chain_flags: set[str] = set()
        if chain.review_status in _NON_STANDARD_CHAIN_STATUSES:
            chain_flags.add(f"chain_status:{chain.review_status}")
        if chain.flags:
            for flag in chain.flags.split(","):
                if flag.strip():
                    chain_flags.add(f"parser_flag:{flag.strip()}")

        for node in chain.nodes:
            rendered_name, name_source, name_flags = _render_node_name(
                node,
                persons,
                narrator_en_by_entry,
                effective_by_node.get(node.id, (None, "missing_rank1", "machine")),
            )
            phrase = _phrase_en(node.transmission_phrase)
            node_flags = list(name_flags)
            if phrase == "via":
                node_flags.append("unmapped_transmission_phrase")
            rendered_nodes.append(
                RenderedChainNode(
                    node_id=node.id,
                    position=node.position,
                    source_token=node.raw_token,
                    rendered_name=rendered_name,
                    name_source=name_source,
                    phrase_en=phrase,
                    risk_flags=node_flags,
                )
            )
            node_parts.append(rendered_name if node.position == 0 else f"{phrase} {rendered_name}")
            chain_flags.update(node_flags)

        prefix = f"Chain {chain.chain_number}"
        text = f"{prefix}: " + "; ".join(node_parts) + "."
        rendered_chains.append(
            RenderedChain(
                chain_id=chain.id,
                chain_number=chain.chain_number,
                text=text,
                review_status=chain.review_status,
                parser_flags=chain.flags,
                nodes=rendered_nodes,
                risk_flags=sorted(chain_flags),
            )
        )
        all_flags.update(chain_flags)

    return IsnadRenderResult(
        hadith_id=hadith.id,
        public_id=hadith.public_id,
        text=" ".join(chain.text for chain in rendered_chains),
        chains=rendered_chains,
        risk_flags=sorted(all_flags),
    )


def _phrase_en(phrase: str | None) -> str:
    if not phrase:
        return "from"
    return _TRANSMISSION_PHRASES.get(normalise_arabic_persian(phrase), "via")


def _render_node_name(
    node: ChainNode,
    persons: dict[int, Person],
    narrator_en_by_entry: dict[int, str],
    effective: tuple[int | None, str, str],
) -> tuple[str, str, list[str]]:
    person_id, status, source = effective
    flags: list[str] = []
    if person_id is not None and person_id in persons:
        person = persons[person_id]
        if person.primary_entry_id and narrator_en_by_entry.get(person.primary_entry_id):
            return narrator_en_by_entry[person.primary_entry_id], f"person_{source}_narrator_en", flags
        flags.append("name_preserved_arabic")
        return person.canonical_name_ar, f"person_{source}_arabic", flags

    if node.narrator and node.narrator.canonical_name_en:
        return node.narrator.canonical_name_en, "chain_node_narrator_en", flags

    flags.append(f"unresolved_name:{status}")
    flags.append("name_preserved_arabic")
    return node.raw_token, "chain_node_raw_arabic", flags

