"""Reproducible review ledger for retained al-Tusi chain cases.

The tokenizer intentionally fails closed on prose spill and route multiplicity.
This module records the disposition of every such Tahdhib/Istibsar chain without
editing the printed isnad or pretending that a parser limitation is a narrator.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.models import Book, Chain, ChainNode, Hadith
from eshia_research.rijal.mashyakha import TUSI_SOURCE_BOOK_IDS


AUDIT_SCHEMA_VERSION = "tusi-chain-review-v1"
_SOURCE_ANOMALY_MARKERS = (
    "بسم الله الرحمن الرحيم",
    "القبطية : واحد القباط",
    "والحديث فيه",
)


def _flags(value: str | None) -> set[str]:
    return {flag for flag in (value or "").split(",") if flag}


def _suspicious_disposition(raw_isnad: str) -> tuple[str, str, str]:
    if any(marker in raw_isnad for marker in _SOURCE_ANOMALY_MARKERS):
        return (
            "retained_review_only",
            "suspect_text",
            "The preserved isnad contains an editorial/page-boundary insertion; no safe "
            "automatic correction is supported by this row alone.",
        )
    return (
        "retained_review_only",
        "parser_boundary",
        "The literal source is preserved, but prose or attribution syntax entered a narrator "
        "token. The chain remains excluded from automatic identity resolution.",
    )


def _multi_route_classification(flags: set[str]) -> tuple[str, str]:
    if "suspicious_token" in flags:
        return (
            "multi_route_with_suspicious_overlap",
            "Parallel-route syntax is present and the same chain is covered by the suspicious-case ledger.",
        )
    if "mursal_opening" in flags and "no_imam_terminal" in flags:
        return (
            "mursal_parallel_routes_without_explicit_terminal",
            "The source preserves multiple routes from an abbreviated opening without an explicit terminal Imam.",
        )
    if "mursal_opening" in flags:
        return (
            "mursal_parallel_routes",
            "The source preserves multiple routes from an abbreviated opening.",
        )
    if "no_imam_terminal" in flags:
        return (
            "parallel_routes_without_explicit_terminal",
            "The source preserves route multiplicity but does not print an explicit terminal Imam in this chain fragment.",
        )
    return (
        "parallel_routes_with_explicit_terminal",
        "The source preserves multiple or convergent routes with an explicit terminal attribution.",
    )


def build_tusi_chain_review(db: Session, *, audit_date: str) -> dict:
    rows = db.execute(
        select(
            Book.source_book_id,
            Hadith.public_id,
            Hadith.source_url,
            Chain.id,
            Chain.chain_number,
            Chain.raw_isnad,
            Chain.flags,
            Chain.review_status,
        )
        .join(Hadith, Hadith.book_id == Book.id)
        .join(Chain, Chain.hadith_id == Hadith.id)
        .where(
            Book.source_book_id.in_(TUSI_SOURCE_BOOK_IDS),
            (
                Chain.flags.contains("suspicious_token")
                | Chain.flags.contains("multi_route")
            ),
        )
        .order_by(Book.source_book_id, Hadith.sequence_in_book, Chain.chain_number)
    ).all()
    chain_ids = [row.id for row in rows]
    tokens_by_chain: dict[int, list[dict]] = {chain_id: [] for chain_id in chain_ids}
    if chain_ids:
        for node in db.scalars(
            select(ChainNode)
            .where(ChainNode.chain_id.in_(chain_ids))
            .order_by(ChainNode.chain_id, ChainNode.position)
        ):
            tokens_by_chain[node.chain_id].append(
                {
                    "position": node.position,
                    "raw": node.raw_token,
                    "normalised": node.token_normalised,
                    "node_type": node.node_type,
                }
            )

    suspicious: list[dict] = []
    multi_route: list[dict] = []
    for row in rows:
        flags = _flags(row.flags)
        common = {
            "source_book_id": row.source_book_id,
            "public_id": row.public_id,
            "source_url": row.source_url,
            "chain_id": row.id,
            "chain_number": row.chain_number,
            "raw_isnad": row.raw_isnad,
            "flags": sorted(flags),
            "review_status": row.review_status,
            "tokens": tokens_by_chain[row.id],
        }
        if "suspicious_token" in flags:
            disposition, classification, rationale = _suspicious_disposition(row.raw_isnad)
            suspicious.append(
                {
                    **common,
                    "disposition": disposition,
                    "classification": classification,
                    "rationale": rationale,
                }
            )
        if "multi_route" in flags:
            classification, rationale = _multi_route_classification(flags)
            multi_route.append(
                {
                    **common,
                    "disposition": "retained_review_only",
                    "classification": classification,
                    "rationale": rationale,
                }
            )

    def counts(items: list[dict], key: str) -> dict[str, int]:
        return dict(sorted(Counter(item[key] for item in items).items()))

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit_date": audit_date,
        "scope": list(TUSI_SOURCE_BOOK_IDS),
        "policy": {
            "literal_isnad_preserved": True,
            "review_only_rows_feed_identity_resolution": False,
            "multi_route_collapsed": False,
        },
        "summary": {
            "suspicious_chains": len(suspicious),
            "suspicious_by_book": counts(suspicious, "source_book_id"),
            "suspicious_by_classification": counts(suspicious, "classification"),
            "multi_route_chains": len(multi_route),
            "multi_route_by_book": counts(multi_route, "source_book_id"),
            "multi_route_by_classification": counts(multi_route, "classification"),
        },
        "suspicious_cases": suspicious,
        "multi_route_cases": multi_route,
    }


def write_tusi_chain_review(report: dict, json_path: str | Path, markdown_path: str | Path) -> None:
    json_destination = Path(json_path)
    markdown_destination = Path(markdown_path)
    json_destination.parent.mkdir(parents=True, exist_ok=True)
    markdown_destination.parent.mkdir(parents=True, exist_ok=True)
    json_destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    summary = report["summary"]
    lines = [
        "# Al-Tusi retained-chain review",
        "",
        f"Date: {report['audit_date']}",
        "",
        "The literal isnad is authoritative. This audit does not collapse parallel routes, "
        "invent missing terminals, or admit parser-spill tokens into automatic identity resolution.",
        "",
        "## Counts",
        "",
        f"- suspicious chains reviewed: **{summary['suspicious_chains']}**",
        f"- retained multi-route chains classified: **{summary['multi_route_chains']}**",
        f"- suspicious by book: `{summary['suspicious_by_book']}`",
        f"- multi-route by book: `{summary['multi_route_by_book']}`",
        "",
        "The adjacent JSON ledger records every chain, source URL, literal isnad, token list, "
        "classification, disposition, and rationale.",
        "",
        "## Suspicious-chain decisions",
        "",
        "| Book | Hadith | Chain | Classification | Disposition |",
        "|---|---|---:|---|---|",
    ]
    for item in report["suspicious_cases"]:
        lines.append(
            f"| `{item['source_book_id']}` | [{item['public_id']}]({item['source_url']}) | "
            f"`{item['chain_id']}` | "
            f"`{item['classification']}` | `{item['disposition']}` |"
        )
    lines.extend(
        [
            "",
            "## Multi-route policy",
            "",
            "All retained multi-route rows remain review-only. Their route multiplicity is "
            "preserved in the literal text and is never flattened into a fabricated linear chain.",
            "",
            f"Classification totals: `{summary['multi_route_by_classification']}`",
            "",
        ]
    )
    markdown_destination.write_text("\n".join(lines), encoding="utf-8")
