"""Build Chain/ChainNode rows from extracted hadiths' isnad_raw text."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from eshia_research.corpus import CANONICAL_FOUR_BOOK_SOURCE_IDS
from eshia_research.isnad.tokenizer import tokenize_isnad
from eshia_research.models import Book, Chain, ChainNode, ChainNodeCandidate, Hadith

REJECTED_HADITH_STATUS = "rejected_non_hadith_fragment"


@dataclass
class ChainIndexStats:
    hadiths: int = 0
    chains: int = 0
    nodes: int = 0
    needs_review: int = 0
    flag_counts: Counter = field(default_factory=Counter)

    @property
    def clean_ratio(self) -> float:
        return 0.0 if not self.chains else 1 - (self.needs_review / self.chains)


def rebuild_chain_index(
    db: Session,
    *,
    source_book_ids: tuple[str, ...] | list[str] | None = None,
    book_ids: list[int] | None = None,
    parser_version: str = "isnad_v1",
    commit: bool = True,
) -> ChainIndexStats:
    """Rebuild chains for the selected books' hadiths from isnad_raw.

    Deletes and recreates — chains are derived data; hadiths.isnad_raw is
    the source of truth.
    """
    query = db.query(Book.id)
    if book_ids:
        query = query.filter(Book.id.in_(book_ids))
    else:
        selected = tuple(source_book_ids or CANONICAL_FOUR_BOOK_SOURCE_IDS)
        query = query.filter(Book.source_book_id.in_(selected))
    selected_book_ids = [row[0] for row in query.all()]

    stats = ChainIndexStats()
    if not selected_book_ids:
        return stats

    hadith_ids_subq = select(Hadith.id).where(Hadith.book_id.in_(selected_book_ids))
    chain_ids_subq = select(Chain.id).where(Chain.hadith_id.in_(hadith_ids_subq))
    node_ids_subq = select(ChainNode.id).where(ChainNode.chain_id.in_(chain_ids_subq))
    db.execute(delete(ChainNodeCandidate).where(ChainNodeCandidate.chain_node_id.in_(node_ids_subq)))
    db.execute(delete(ChainNode).where(ChainNode.chain_id.in_(chain_ids_subq)))
    db.execute(delete(Chain).where(Chain.hadith_id.in_(hadith_ids_subq)))
    # Rebuilding the hadith index replaces hadith rows (new ids), which can
    # strand chains pointing at deleted hadiths — sqlite doesn't enforce the
    # FK here. Sweep those (and their nodes/candidates) regardless of book
    # selection.
    orphan_chain_ids = select(Chain.id).where(~Chain.hadith_id.in_(select(Hadith.id)))
    orphan_node_ids = select(ChainNode.id).where(ChainNode.chain_id.in_(orphan_chain_ids))
    db.execute(delete(ChainNodeCandidate).where(ChainNodeCandidate.chain_node_id.in_(orphan_node_ids)))
    db.execute(delete(ChainNode).where(ChainNode.chain_id.in_(orphan_chain_ids)))
    db.execute(delete(Chain).where(~Chain.hadith_id.in_(select(Hadith.id))))
    # Candidates whose node vanished in an earlier partial rebuild.
    db.execute(
        delete(ChainNodeCandidate).where(
            ~ChainNodeCandidate.chain_node_id.in_(select(ChainNode.id))
        )
    )
    db.flush()

    hadiths = (
        db.query(Hadith.id, Hadith.isnad_raw)
        .filter(
            Hadith.book_id.in_(selected_book_ids),
            Hadith.review_status != REJECTED_HADITH_STATUS,
            Hadith.isnad_raw.isnot(None),
        )
        .order_by(Hadith.id)
        .all()
    )
    for hadith_id, isnad_raw in hadiths:
        stats.hadiths += 1
        tokenized = tokenize_isnad(isnad_raw)
        for chain_number, parsed in enumerate(tokenized, start=1):
            needs_review = parsed.needs_review
            chain = Chain(
                hadith_id=hadith_id,
                chain_number=chain_number,
                raw_isnad=isnad_raw,
                parser_version=parser_version,
                node_count=len(parsed.tokens),
                flags=",".join(sorted(parsed.flags)) or None,
                review_status="needs_review" if needs_review else "pending",
            )
            db.add(chain)
            db.flush()  # chain.id for the nodes
            stats.chains += 1
            stats.needs_review += int(needs_review)
            stats.flag_counts.update(parsed.flags)
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
                stats.nodes += 1
        # Chunked commits keep SQLite write locks short — a crawl may be
        # writing to the same database file concurrently.
        if commit and stats.hadiths % 500 == 0:
            db.commit()

    if commit:
        db.commit()
    return stats
