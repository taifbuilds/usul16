"""Conservative repairs for known hadith split failure classes."""

from __future__ import annotations

import datetime as dt
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from eshia_research.models import Book, Hadith, HadithSplitReview
from eshia_research.normalise import normalise_arabic_persian

ARABIC_RANGE = "\u0621-\u064a"
AN = "\u0639\u0646"
BIN = "\u0628\u0646"
FI = "\u0641\u064a"

COMMENTARY_STARTS = (
    "\u0642\u0648\u0644\u0647",  # qawlihi
    "\u0642\u064a\u0644",  # qila
    "\u0647\u0643\u0630\u0627",  # hakadha
    "\u0627\u0644\u0639\u0646\u0643\u0628\u0648\u062a",  # al-ankabut
    "\u062b\u0642\u0641\u0647",
    "\u0639\u0644\u064a\u0647 \u0623\u062c\u0631\u0627",
    "\u0644\u0647\u0645\u0627 \u0645\u0646\u0639\u0647",
    "\u0648 \u0627\u0639\u0644\u0645",
    "\u0648 \u0627\u0646 \u062a\u0637\u0626\u0648\u0627",
)
CONTINUATION_STARTS = (
    "\u0642\u0627\u0644:",
    "\u0648\u0642\u0627\u0644",
    "\u0648 \u0642\u0627\u0644",
    "\u0648 \u0641\u064a \u0631\u0648\u0627\u064a\u0629",
)
SAFE_FI_PREFIXES = (
    "\u0641\u064a \u062d\u062f\u064a\u062b",
    "\u0641\u064a \u0642\u0648\u0644",
    "\u0641\u064a \u0642\u0648\u0644\u0647",
    "\u0641\u064a \u062e\u0637\u0628\u0629",
    "\u0641\u064a \u062e\u0637\u0628\u062a\u0647",
    "\u0641\u064a \u0627\u0644\u0631\u062c\u0644",
    "\u0641\u064a \u0631\u062c\u0644",
    "\u0641\u064a \u0627\u0644\u0645\u0631\u0623\u0629",
    "\u0641\u064a \u0627\u0644\u0645\u0627\u0621",
    "\u0641\u064a \u0627\u0644\u0634\u0627\u0629",
    "\u0641\u064a \u0645\u064a\u0632\u0627\u0628",
    "\u0641\u064a \u0627\u0644\u0645\u0637\u0644\u0642\u0629",
    "\u0641\u064a \u0627\u0644\u0623\u0645\u0629",
    "\u0641\u064a \u0627\u0644\u0643\u0644\u0628",
    "\u0641\u064a \u0627\u0644\u0623\u0646\u0641",
    "\u0641\u064a \u0627\u0644\u0646\u0637\u0641\u0629",
    "\u0641\u064a \u0627\u0644\u0634\u0647\u0648\u062f",
    "\u0641\u064a \u0627\u0644\u0635\u0644\u0627\u0629",
    "\u0641\u064a \u0627\u0644\u062f\u0639\u0627\u0621",
    "\u0641\u064a \u0627\u0644\u062d\u0631\u0645\u064a\u0646",
    "\u0641\u064a \u0648\u0635\u064a\u0629",
    "\u0641\u064a \u062a\u0633\u0645\u064a\u0629",
    "\u0641\u064a \u0642\u0635",
)

AN_REPORT_RE = re.compile(r"\s+(?:\u0623\u0646|\u0627\u0646|\u0625\u0646)(?:\u0647|\u0647\u0627|\u0647\u0645\u0627)?(?=\s)")
FI_REPORT_RE = re.compile(r"\s+\u0641\u064a\s+")
TERMINAL_RE = re.compile(
    rf"(?<![{ARABIC_RANGE}])("
    r"[\u0639\u0635]|"
    r"\u0639\u0644\u064a\u0647\s+\u0627\u0644\u0633\u0644\u0627\u0645|"
    r"\u0635\u0644\u0649\s+\u0627\u0644\u0644\u0647\s+\u0639\u0644\u064a\u0647\s+\u0648\s+\u0622\u0644\u0647"
    rf")(?![{ARABIC_RANGE}])"
)
SPEECH_AFTER_TERMINAL_RE = re.compile(
    r"^\s*(?:"
    r"\u064a\u0642\u0648\u0644|"
    r"\u064a\u0642\u0648\u0644\u0627\u0646|"
    r"\u0642\u0627\u0644\u0648\u0627|"
    r"\u0642\u0627\u0644\u0627|"
    r"\u0642\u0627\u0644"
    r")(?:\s*[:\uff1a])?"
)
QAL_COLON_OPENING_RE = re.compile(r"^(.{2,80}?\u0642\u0627\u0644\s*[:\uff1a])\s+")
RAFA_RE = re.compile(
    r"\s+(?:\u0631\u0641\u0639\u0647|\u0631\u0641\u0639\u0647\u0627|\u0631\u0641\u0639\u0647\u0645)\s+"
)


@dataclass(frozen=True)
class MissingIsnadSplitProposal:
    isnad_raw: str
    matn_raw: str
    method: str


@dataclass
class MissingIsnadRepairStats:
    rows_seen: int = 0
    proposed: int = 0
    applied: int = 0
    skipped: int = 0
    method_counts: Counter = field(default_factory=Counter)
    skip_counts: Counter = field(default_factory=Counter)


def _is_mark(char: str) -> bool:
    codepoint = ord(char)
    return (
        unicodedata.category(char) in {"Mn", "Me"}
        or char == "\u0640"
        or 0x0610 <= codepoint <= 0x061A
        or 0x06D6 <= codepoint <= 0x06ED
    )


def _strip_with_map(text: str) -> tuple[str, list[int]]:
    stripped: list[str] = []
    mapping: list[int] = []
    for index, char in enumerate(text or ""):
        if _is_mark(char):
            continue
        stripped.append(char)
        mapping.append(index)
    return "".join(stripped), mapping


def _raw_boundary(raw: str, mapping: list[int], plain_index: int) -> int:
    if plain_index <= 0:
        index = 0
    elif plain_index >= len(mapping):
        index = len(raw)
    else:
        index = mapping[plain_index - 1] + 1
    while index < len(raw) and (raw[index] in " \t\r\n\u200c\u200d" or _is_mark(raw[index])):
        index += 1
    return index


def _chain_score(text: str) -> int:
    return (
        text.count(AN)
        + text.count(BIN)
        + text.count("\u062d\u062f\u062b")
        + text.count("\u0623\u062e\u0628\u0631")
        + text.count("\u0627\u062e\u0628\u0631")
        + text.count("\u0631\u0641\u0639")
        + text.count("\u0631\u0648\u064a")
    )


def _starts_any(text: str, prefixes: tuple[str, ...]) -> bool:
    stripped = text.strip()
    return any(stripped.startswith(prefix) for prefix in prefixes)


def _has_terminal_marker(text: str) -> bool:
    return bool(TERMINAL_RE.search(text))


def _proposal_from_boundary(raw: str, mapping: list[int], plain_index: int, method: str) -> MissingIsnadSplitProposal | None:
    boundary = _raw_boundary(raw, mapping, plain_index)
    isnad = raw[:boundary].strip()
    matn = raw[boundary:].strip()
    if not isnad or len(matn) < 3:
        return None
    return MissingIsnadSplitProposal(isnad_raw=isnad, matn_raw=matn, method=method)


def propose_missing_isnad_split(raw_text: str) -> tuple[MissingIsnadSplitProposal | None, str]:
    """Propose a split for rows where the whole hadith is currently in matn_raw.

    The rules are intentionally narrow and ordered from safest to broadest:
    commentarial fragments and obvious continuations are skipped; explicit
    topic/report markers are handled before terminal-marker fallbacks; and
    bare ``an`` report splitting only fires before any Imam/Prophet terminal
    marker appears in the prefix.
    """
    raw = raw_text or ""
    plain, mapping = _strip_with_map(raw)
    stripped = plain.strip()
    if _starts_any(stripped, COMMENTARY_STARTS):
        return None, "skip_commentary"
    if _starts_any(stripped, CONTINUATION_STARTS):
        return None, "skip_continuation"

    match = QAL_COLON_OPENING_RE.match(stripped)
    if match and _chain_score(match.group(1)) == 0:
        proposal = _proposal_from_boundary(raw, mapping, match.end(1), "one_name_qal_colon")
        if proposal:
            return proposal, proposal.method

    for match in FI_REPORT_RE.finditer(stripped):
        prefix = stripped[: match.start()].strip()
        suffix = stripped[match.start() :].strip()
        if len(prefix) <= 850 and _chain_score(prefix) >= 2 and _starts_any(suffix, SAFE_FI_PREFIXES):
            proposal = _proposal_from_boundary(raw, mapping, match.start(), "fi_topic")
            if proposal:
                return proposal, proposal.method

    for match in RAFA_RE.finditer(stripped):
        prefix = stripped[: match.end()].strip()
        suffix = stripped[match.end() :].strip()
        if _chain_score(prefix) >= 1 and (
            suffix.startswith(FI + " ")
            or suffix.startswith("\u062f\u0639\u0627\u0621")
            or suffix.startswith("\u0645\u062b\u0644")
        ):
            proposal = _proposal_from_boundary(raw, mapping, match.end(), "rafa_topic")
            if proposal:
                return proposal, proposal.method

    for match in AN_REPORT_RE.finditer(stripped):
        prefix = stripped[: match.start()].strip()
        if len(prefix) <= 650 and _chain_score(prefix) >= 2 and not _has_terminal_marker(prefix):
            proposal = _proposal_from_boundary(raw, mapping, match.start(), "an_report")
            if proposal:
                return proposal, proposal.method

    for match in TERMINAL_RE.finditer(stripped):
        prefix = stripped[: match.end()].strip()
        suffix = stripped[match.end() :]
        if len(prefix) > 950 or _chain_score(prefix) < 2:
            continue
        next_words = suffix.strip()[:80]
        if next_words.startswith(AN) or next_words.startswith("\u0648 " + AN):
            continue
        end = match.end()
        speech_match = SPEECH_AFTER_TERMINAL_RE.match(suffix)
        if speech_match:
            end = match.end() + speech_match.end()
        proposal = _proposal_from_boundary(raw, mapping, end, "terminal_marker")
        if proposal:
            return proposal, proposal.method

    return None, "no_proposal"


def repair_missing_isnad_splits(
    db: Session,
    *,
    source_book_id: str,
    apply: bool = False,
    reviewer: str = "codex-missing-isnad-high-confidence-pass",
    split_version: str = "missing_isnad_high_conf_v1",
) -> MissingIsnadRepairStats:
    book = db.query(Book).filter(Book.source_book_id == source_book_id).one()
    rows = (
        db.query(Hadith, HadithSplitReview)
        .outerjoin(HadithSplitReview, HadithSplitReview.hadith_id == Hadith.id)
        .filter(
            Hadith.book_id == book.id,
            (Hadith.isnad_raw.is_(None)) | (Hadith.isnad_raw == ""),
            (HadithSplitReview.id.is_(None)) | (HadithSplitReview.review_status == "unreviewed"),
        )
        .order_by(Hadith.sequence_in_book)
        .all()
    )

    stats = MissingIsnadRepairStats(rows_seen=len(rows))
    now = dt.datetime.now(dt.timezone.utc)
    for hadith, review in rows:
        proposal, reason = propose_missing_isnad_split(hadith.matn_raw or "")
        if proposal is None:
            stats.skipped += 1
            stats.skip_counts[reason] += 1
            continue

        stats.proposed += 1
        stats.method_counts[proposal.method] += 1
        if not apply:
            continue

        hadith.isnad_raw = proposal.isnad_raw
        hadith.isnad_normalised = normalise_arabic_persian(proposal.isnad_raw)
        hadith.matn_raw = proposal.matn_raw
        hadith.matn_normalised = normalise_arabic_persian(proposal.matn_raw)
        hadith.extraction_confidence = max(hadith.extraction_confidence or 0, 94)
        hadith.updated_at = now

        if review is None:
            review = HadithSplitReview(hadith_id=hadith.id)
            db.add(review)
        review.approved_isnad_raw = proposal.isnad_raw
        review.approved_matn_raw = proposal.matn_raw
        review.review_status = "approved"
        review.reviewer = reviewer
        review.notes = f"High-confidence missing-isnad repair via {proposal.method}."
        review.split_version = split_version
        review.updated_at = now
        stats.applied += 1

    if apply:
        db.commit()
    return stats
