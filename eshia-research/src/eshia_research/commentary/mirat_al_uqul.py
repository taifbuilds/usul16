"""Index al-Majlisi's *Mir'at al-'Uqul* against the local al-Kafi corpus.

The eShia edition deliberately prints al-Kafi reports in ordinary ``p`` tags
and al-Majlisi's notes in ``span.FootNote`` tags.  Treating the whole rendered
page as one text stream would mingle a report with the preceding report's
continued explanation at page boundaries.  This module keeps those two source
layers separate before any matching is attempted.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import re
from typing import Iterable

from bs4 import BeautifulSoup, Tag
from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.commentary.alignment import (
    ChapterRun,
    align_chapters,
    propose_by_ordinal,
)
from eshia_research.commentary.matching import (
    ARABIC_WORD_RE as _ARABIC_WORD_RE,
    best_text_candidate,
    clear_hadith_token_cache,
    comparable_tokens,
    hadith_tokens,
    hadith_word_index,
    incipit_aligned,
    score_report_text,
)
from eshia_research.corpus import AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID
from eshia_research.models import Book, Hadith, HadithCommentary, Page
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.thaqalayn_importer import match_norm, match_words


MIRAT_AL_UQUL_SOURCE_BOOK_ID = "71429"
MIRAT_AL_UQUL_SOURCE_KEY = "mirat-al-uqul"
MIRAT_AL_UQUL_TITLE_AR = "مرآة العقول في شرح أخبار آل الرسول"
MIRAT_AL_UQUL_AUTHOR_AR = "العلامة المجلسي"
# Short forms: the reader shows these beside the Arabic, so they name the work
# and its author rather than transliterating the full title.
MIRAT_AL_UQUL_TITLE_EN = "Mir'at al-'Uqul"
MIRAT_AL_UQUL_AUTHOR_EN = "al-'Allama al-Majlisi"
MIRAT_AL_UQUL_MATCHER_VERSION = "mirat_al_uqul_v4"
_SECTION_HEADING_RE = re.compile(r"^(?:\u06a9\u062a\u0627\u0628|\u0628\u0627\u0628)\s+\S+")
# Brackets, quotes and bidi marks the edition wraps chapter titles in.
_HEADING_WRAPPER_CHARS = "()[]{}\u00ab\u00bb\u200e\u200f\u061c*\u2022. \t"

_NUMBERED_REPORT_RE = re.compile(r"^\s*(?P<number>[0-9٠-٩۰-۹]+)\s*[ـ\-–]\s*(?P<text>.+)$")
_HEADER_START_RE = re.compile(r"(?:^|[.!؟])\s*(?P<label>الحديث\s+)")
_HADITH_MENTION_RE = re.compile(r"الحديث\s+")
_HEADER_COLONS = {":", "：", "؛"}

_UNITS = {
    "الأول": 1,
    "الاول": 1,
    "الحادي": 1,
    "الحادية": 1,
    "الثاني": 2,
    "الثانية": 2,
    "الثالث": 3,
    "الثالثة": 3,
    "الرابع": 4,
    "الرابعة": 4,
    "الخامس": 5,
    "الخامسة": 5,
    "السادس": 6,
    "السادسة": 6,
    "السابع": 7,
    "السابعة": 7,
    "الثامن": 8,
    "الثامنة": 8,
    "التاسع": 9,
    "التاسعة": 9,
    "العاشر": 10,
    "العاشرة": 10,
}
_TENS = {
    "عشر": 10,
    "عشرة": 10,
    "العشرون": 20,
    "الثلاثون": 30,
    "الأربعون": 40,
    "الخمسون": 50,
    "الستون": 60,
    "السبعون": 70,
    "الثمانون": 80,
    "التسعون": 90,
    "المائة": 100,
    "المئة": 100,
}
_UNITS = {normalise_arabic_persian(key): value for key, value in _UNITS.items()}
_TENS = {normalise_arabic_persian(key): value for key, value in _TENS.items()}
_HADITH_WORD = normalise_arabic_persian("الحديث")
_BOOK_PREFIX = normalise_arabic_persian("كتاب ")
_CHAPTER_PREFIX = normalise_arabic_persian("باب ")


@dataclass
class TextPart:
    text: str
    volume: int
    page: int


@dataclass
class SourceReport:
    section_title: str | None
    printed_number: int
    parts: list[TextPart] = field(default_factory=list)
    # Chapter titles are not unique in a 26-volume book — "باب نادر" alone
    # recurs dozens of times. Reports are therefore keyed by *which* run of a
    # title they belong to, never by the title text alone.
    section_occurrence: int = 1

    @property
    def text(self) -> str:
        return _clean_text(" ".join(part.text for part in self.parts))


@dataclass
class CommentaryPassage:
    source_sequence: int
    source_label: str
    section_title: str | None
    printed_number: int | None
    parts: list[TextPart] = field(default_factory=list)
    section_occurrence: int = 1

    @property
    def text(self) -> str:
        return _clean_text(" ".join(part.text for part in self.parts))

    @property
    def volume_start(self) -> int:
        return self.parts[0].volume

    @property
    def volume_end(self) -> int:
        return self.parts[-1].volume

    @property
    def page_start(self) -> int:
        return self.parts[0].page

    @property
    def page_end(self) -> int:
        return self.parts[-1].page


@dataclass
class CommentaryIndexStats:
    pages_seen: int = 0
    source_reports: int = 0
    extracted: int = 0
    matched: int = 0
    needs_review: int = 0
    unmatched: int = 0
    malformed: int = 0
    aligned: int = 0
    """Subset of ``matched`` placed by chapter position rather than by text."""


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    translated = value.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789"))
    try:
        return int(translated)
    except ValueError:
        return None


def _normalise_ordinal_word(value: str) -> str:
    value = normalise_arabic_persian(value)
    if value.startswith("وال"):
        return value[1:]
    if value.startswith("و") and value[1:] in _UNITS | _TENS:
        return value[1:]
    return value


def _ordinal_value(words: list[str]) -> int | None:
    if not words:
        return None
    values: list[int] = []
    for word in words:
        key = _normalise_ordinal_word(word)
        value = _UNITS.get(key, _TENS.get(key))
        if value is None:
            return None
        values.append(value)
    if len(values) == 1:
        return values[0]
    if values.count(100) > 1 or any(value not in (100,) and value > 99 for value in values):
        return None
    return sum(values)


def parse_ordinal_header(text: str) -> tuple[str, int | None]:
    """Return the visible ``الحديث ...`` label and its integer when readable."""
    words = _ARABIC_WORD_RE.findall(text)
    if not words or normalise_arabic_persian(words[0]) != _HADITH_WORD:
        return _clean_text(text), None
    ordinal_words = words[1:8]
    best_count = 0
    best_value: int | None = None
    for count in range(1, len(ordinal_words) + 1):
        value = _ordinal_value(ordinal_words[:count])
        if value is not None:
            best_count = count
            best_value = value
    label_words = words[: 1 + best_count] if best_count else words[:1]
    return " ".join(label_words), best_value


def _section_heading(text: str) -> str | None:
    candidate = _clean_text(text).strip(_HEADING_WRAPPER_CHARS)
    normalised = normalise_arabic_persian(candidate)
    if len(normalised) > 350:
        return None
    if _SECTION_HEADING_RE.match(normalised):
        return candidate
    return None


def _is_section_heading(text: str) -> bool:
    return _section_heading(text) is not None


def _content_cell(page: Page) -> Tag | None:
    if not page.html_raw:
        return None
    soup = BeautifulSoup(page.html_raw, "lxml")
    cell = soup.find("td", class_="book-page-show")
    if cell is None:
        return None
    menu = cell.find("div", class_="sticky-menue")
    if menu is not None:
        menu.extract()
    return cell


def _header_starts(text: str) -> list[int]:
    """Offsets where a new «الحديث ...» passage begins.

    A header normally opens the span or follows a full stop. But eShia also
    runs the chapter title straight into it with no punctuation —
    «...والسبيل فيهم مقيم الحديث الأول : ضعيف» — and those passages were being
    swallowed as continuations of the previous sharh. The printed header form
    ends in a colon, which distinguishes a real header from al-Majlisi
    referring back to «الحديث الأول» inside his own prose.
    """
    starts: list[int] = []
    for match in _HADITH_MENTION_RE.finditer(text):
        start = match.start()
        before = text[:start].rstrip()
        opens_span = not before or before[-1] in ".!؟"
        if opens_span:
            starts.append(start)
            continue
        label, number = parse_ordinal_header(text[start:])
        if number is None:
            continue
        rest = text[start + len(label):].lstrip()
        if rest[:1] in _HEADER_COLONS:
            starts.append(start)
    return starts


def _commentary_segments(text: str) -> list[tuple[str, str]]:
    """Split one FootNote span into its leading continuation and new headers."""
    starts = _header_starts(text)
    if not starts:
        return [("continuation", _clean_text(text))] if _clean_text(text) else []
    segments: list[tuple[str, str]] = []
    prefix = _clean_text(text[: starts[0]])
    if prefix:
        segments.append(("continuation", prefix))
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        segment = _clean_text(text[start:end])
        if segment:
            segments.append(("header", segment))
    return segments


def _reassign_carryover_passages(
    passages: list[CommentaryPassage],
    reports: dict[tuple[str, int, int], "SourceReport"],
) -> int:
    """Give back the sharh that belongs to the chapter that just ended.

    eShia prints the al-Kafi text at the head of the page and al-Majlisi's
    commentary at its foot, so the footnote area *lags* the main text. On the
    page where a new chapter opens, the sharh below it is still finishing the
    previous chapter — which is why a run reads «التاسع، الأول، الثاني …»,
    with the ninth arriving before the first.

    Left alone those carry-over passages are filed under the wrong chapter and,
    sharing an ordinal with the chapter's own passage, they take its report and
    win the claim on iteration order — publishing the wrong sharh and
    discarding the right one as a duplicate.
    """
    runs: dict[int, list[CommentaryPassage]] = {}
    for passage in passages:
        runs.setdefault(passage.section_occurrence, []).append(passage)

    # Every chapter run in the book, including ones the commentator passed over
    # in silence — the chapter a carry-over belongs to may have no passage of
    # its own on this page.
    titles = {occ: report.section_title for (_key, occ, _number), report in reports.items()}
    for occurrence, members in runs.items():
        titles.setdefault(occurrence, members[0].section_title)
    ordered = sorted(titles)
    previous_of = {occ: ordered[i - 1] for i, occ in enumerate(ordered) if i > 0}

    moved = 0
    for occurrence in sorted(runs):
        members = runs[occurrence]
        first_opener = next(
            (i for i, p in enumerate(members) if p.printed_number == 1), None
        )
        if not first_opener:  # None, or already at index 0
            continue
        leading = members[:first_opener]
        # Only a genuine carry-over: every one of them numbers above the
        # opener, so none of them can belong to this chapter.
        if any(p.printed_number is None or p.printed_number <= 1 for p in leading):
            continue
        target = previous_of.get(occurrence)
        if target is None:
            continue
        for passage in leading:
            passage.section_occurrence = target
            passage.section_title = titles.get(target, passage.section_title)
            moved += 1
    return moved


def report_key(section_title: str | None, occurrence: int, number: int) -> tuple[str, int, int]:
    """Identity of one printed report: which chapter run it sits in, and its number."""
    return (normalise_arabic_persian(section_title or ""), occurrence, number)


def extract_mirat_passages(
    pages: Iterable[Page], *, pages_are_ordered: bool = False
) -> tuple[list[CommentaryPassage], dict[tuple[str, int, int], SourceReport], CommentaryIndexStats]:
    """Extract source reports and commentary passages from ordered eShia pages."""
    reports: dict[tuple[str, int, int], SourceReport] = {}
    passages: list[CommentaryPassage] = []
    stats = CommentaryIndexStats()
    current_section: str | None = None
    # eShia reprints the running chapter title at the top of most pages, so a
    # heading only opens a new chapter run when its text actually changes.
    current_section_key: str | None = None
    section_occurrence = 0
    current_report: SourceReport | None = None
    active_commentary: CommentaryPassage | None = None

    # eShia typesets a chapter title as several centred elements in a row —
    # «باب» on its own line, then the rest of the title in one or more further
    # headings. Judged individually neither piece is a chapter title, so the
    # whole heading used to be dropped and its reports were filed under the
    # previous chapter. A run of consecutive heading elements is one title.
    pending_heading: list[str] = []

    def enter_section(heading: str) -> None:
        nonlocal current_section, current_section_key, section_occurrence, current_report
        key = normalise_arabic_persian(heading)
        if key != current_section_key:
            current_section_key = key
            section_occurrence += 1
        current_section = heading
        current_report = None

    def flush_heading() -> None:
        """Close an open heading run and open its chapter, if it names one."""
        nonlocal pending_heading
        if not pending_heading:
            return
        # Later volumes bracket each line of the title — «(باب)» «(فضل البنات)».
        # Each fragment is unwrapped before joining, or the joined title reads
        # "(باب) (فضل البنات)" and stops looking like a chapter heading.
        joined = _clean_text(
            " ".join(part.strip(_HEADING_WRAPPER_CHARS) for part in pending_heading)
        )
        pending_heading = []
        heading = _section_heading(joined)
        if heading is not None:
            enter_section(heading)

    def is_markup_heading(child: Tag) -> bool:
        if child.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            return True
        # eShia's own centred-heading paragraph class (e.g. "Heading2Center").
        return any("Heading" in value for value in (child.get("class") or []))

    if pages_are_ordered:
        ordered_pages = (page for page in pages if page.volume_number is not None)
    else:
        ordered_pages = sorted(
            (page for page in pages if page.volume_number is not None),
            key=lambda page: (page.volume_number or 0, page.page_number),
        )
    for page in ordered_pages:
        cell = _content_cell(page)
        if cell is None:
            continue
        stats.pages_seen += 1
        volume = page.volume_number or 0
        for child in cell.find_all(["p", "span", "h1", "h2", "h3", "h4", "h5", "h6"], recursive=False):
            text = _clean_text(child.get_text(" ", strip=True))
            if not text:
                continue
            classes = set(child.get("class") or [])
            if "FootNote" not in classes and is_markup_heading(child):
                pending_heading.append(text)
                continue
            flush_heading()

            heading = _section_heading(text)
            if "FootNote" in classes:
                # eShia sometimes follows a FootNote span with the same sharh
                # repeated as ordinary paragraphs. It is not a continuation of
                # the preceding copied report.
                current_report = None
                for kind, segment in _commentary_segments(text):
                    if kind == "continuation":
                        if active_commentary is not None:
                            active_commentary.parts.append(TextPart(segment, volume, page.page_number))
                        continue
                    label, printed_number = parse_ordinal_header(segment)
                    active_commentary = CommentaryPassage(
                        source_sequence=len(passages) + 1,
                        source_label=label,
                        section_title=current_section,
                        printed_number=printed_number,
                        parts=[TextPart(segment, volume, page.page_number)],
                        section_occurrence=max(section_occurrence, 1),
                    )
                    passages.append(active_commentary)
                continue

            numbered = _NUMBERED_REPORT_RE.match(text)
            if numbered:
                number = _to_int(numbered.group("number"))
                if number is None:
                    continue
                occurrence = max(section_occurrence, 1)
                key = report_key(current_section, occurrence, number)
                existing = reports.get(key)
                if existing is not None and existing is not current_report:
                    # This number was already closed in this chapter run, so
                    # al-Majlisi has moved into a new chapter whose heading the
                    # source did not mark. Open a fresh run instead of gluing
                    # two unrelated reports into one unmatchable blob.
                    section_occurrence = occurrence + 1
                    occurrence = section_occurrence
                    key = report_key(current_section, occurrence, number)
                    existing = reports.get(key)
                current_report = existing
                if current_report is None:
                    current_report = SourceReport(
                        current_section, number, section_occurrence=occurrence
                    )
                    reports[key] = current_report
                current_report.parts.append(TextPart(text, volume, page.page_number))
                continue

            if heading is not None:
                enter_section(heading)
                continue
            if current_report is not None:
                current_report.parts.append(TextPart(text, volume, page.page_number))

    flush_heading()
    _reassign_carryover_passages(passages, reports)
    stats.source_reports = len(reports)
    stats.extracted = len(passages)
    return passages, reports, stats


# Scoring lives in commentary/matching.py: the same edition-vs-edition
# spelling differences appear in every sharh, so the comparison layer is
# shared rather than reimplemented per source. Thresholds stay here, with
# the caller that has to justify them.
_comparable_tokens = comparable_tokens
_hadith_tokens = hadith_tokens
_incipit_aligned = incipit_aligned
_hadith_token_cache_clear = clear_hadith_token_cache


def _score_report(report: SourceReport | None, hadith: Hadith) -> float | None:
    return score_report_text(report.text if report is not None else None, hadith)


def _source_url(book: Book, passage: CommentaryPassage) -> str:
    base = book.source_url.rstrip("/")
    if re.search(r"/\d+(/\d+)?$", base):
        base = re.sub(r"/\d+(/\d+)?$", "", base)
    return f"{base}/{passage.volume_start}/{passage.page_start}"


def _local_section_index(hadiths: list[Hadith]) -> dict[tuple[str, int], list[Hadith]]:
    index: dict[tuple[str, int], list[Hadith]] = defaultdict(list)
    for hadith in hadiths:
        number = _to_int(hadith.printed_number)
        section = normalise_arabic_persian(hadith.section_title or "")
        if number is not None and section:
            index[(section, number)].append(hadith)
    return index


_hadith_word_index = hadith_word_index


def _best_text_candidate(
    report: SourceReport | None,
    word_index: dict[str, list[Hadith]],
    hadith_by_id: dict[int, Hadith],
) -> tuple[Hadith | None, float | None, float | None]:
    return best_text_candidate(
        report.text if report is not None else None, word_index, hadith_by_id
    )


@dataclass
class _PassageDecision:
    """One passage's verdict, held in memory so alignment can revise it."""

    passage: CommentaryPassage
    report: SourceReport | None
    hadith: Hadith | None
    match_status: str
    match_method: str
    match_score: float | None
    evidence: dict


def build_target_runs(hadiths: list[Hadith]) -> list[ChapterRun]:
    """Split al-Kafi into numbered chapter runs, in printed order.

    A run ends where the chapter title changes or the printed numbering
    restarts — the latter catches chapters the edition prints under a heading
    the crawler recorded identically to the previous one.
    """
    runs: list[ChapterRun] = []
    previous_title: object = object()
    last_ordinal: int | None = None
    for hadith in hadiths:
        title = hadith.section_title or ""
        ordinal = _to_int(hadith.printed_number)
        restarted = (
            ordinal is not None and last_ordinal is not None and ordinal <= last_ordinal
        )
        if title != previous_title or restarted:
            runs.append(ChapterRun(index=len(runs), title=title))
            previous_title = title
            last_ordinal = None
        if ordinal is not None:
            runs[-1].units_by_ordinal.setdefault(ordinal, hadith)
            last_ordinal = ordinal
    return runs


def build_source_runs(passages: list[CommentaryPassage]) -> list[ChapterRun]:
    """Group commentary passages into the chapter runs the extractor found."""
    by_occurrence: dict[int, ChapterRun] = {}
    for passage in passages:
        if passage.printed_number is None:
            continue
        run = by_occurrence.get(passage.section_occurrence)
        if run is None:
            run = ChapterRun(index=passage.section_occurrence, title=passage.section_title or "")
            by_occurrence[passage.section_occurrence] = run
        run.units_by_ordinal.setdefault(passage.printed_number, passage)
    ordered = [by_occurrence[key] for key in sorted(by_occurrence)]
    for position, run in enumerate(ordered):
        run.index = position
    return ordered


# A positional identification is published only when the chapter it rests on
# was pinned by independent text-verified passages, or interpolated between two
# such pins with the chapter titles agreeing. Position alone is never enough.
_MIN_ANCHOR_SUPPORT = 2
_MIN_ANCHOR_SUPPORT_WITH_TITLE = 1
_MIN_TITLE_SIMILARITY = 0.6
_CONTRADICTION_SCORE = 0.35
_MIN_DELTA_AGREEMENT = 0.8


def align_unquoted_passages(
    decisions: list[_PassageDecision],
    hadiths: list[Hadith],
    claimed_hadith_ids: set[int],
) -> int:
    """Place passages by chapter position; returns how many were newly linked."""
    passages = [decision.passage for decision in decisions]
    source_runs = build_source_runs(passages)
    target_runs = build_target_runs(hadiths)
    if not source_runs or not target_runs:
        return 0

    position_by_hadith_id: dict[int, tuple[int, int]] = {}
    for run in target_runs:
        for ordinal, hadith in run.units_by_ordinal.items():
            position_by_hadith_id[hadith.id] = (run.index, ordinal)

    decision_by_sequence = {d.passage.source_sequence: d for d in decisions}
    confirmed: dict[int, tuple[int, int]] = {}
    for decision in decisions:
        if decision.match_status == "matched" and decision.hadith is not None:
            position = position_by_hadith_id.get(decision.hadith.id)
            if position is not None:
                confirmed[decision.passage.source_sequence] = position

    source_titles = [_comparable_tokens(run.title) for run in source_runs]
    target_titles = [_comparable_tokens(run.title) for run in target_runs]

    links = align_chapters(
        source_runs,
        target_runs,
        confirmed,
        lambda passage: passage.source_sequence,
        source_titles=source_titles,
        target_titles=target_titles,
    )
    proposals = propose_by_ordinal(source_runs, target_runs, links)

    linked = 0
    for proposal in proposals:
        decision = decision_by_sequence.get(proposal.source_unit.source_sequence)
        if decision is None or decision.match_status == "matched":
            continue
        if decision.match_status == "malformed":
            continue
        hadith = proposal.target_unit
        if hadith.id in claimed_hadith_ids:
            continue
        link = proposal.link
        trustworthy = (
            link.anchor_support >= _MIN_ANCHOR_SUPPORT
            or (
                link.anchor_support >= _MIN_ANCHOR_SUPPORT_WITH_TITLE
                and link.title_similarity >= _MIN_TITLE_SIMILARITY
            )
            or (link.method == "interpolated" and link.title_similarity >= _MIN_TITLE_SIMILARITY)
        )
        if not trustworthy:
            continue
        # A chapter whose own anchors disagree about the numbering offset is
        # not understood well enough to fill its gaps positionally.
        if link.ordinal_delta_confidence < _MIN_DELTA_AGREEMENT:
            continue
        # Where the commentator *did* reprint the report, an outright
        # disagreement outranks position: leave it for review.
        if decision.report is not None:
            score = _score_report(decision.report, hadith)
            if score is not None and score < _CONTRADICTION_SCORE:
                decision.evidence["alignment_rejected_public_id"] = hadith.public_id
                decision.evidence["alignment_contradiction_score"] = score
                continue
        decision.hadith = hadith
        decision.match_status = "matched"
        decision.match_method = "chapter_sequence_aligned"
        decision.match_score = None
        decision.evidence.update(
            {
                "alignment_method": link.method,
                "alignment_anchor_support": link.anchor_support,
                "alignment_title_similarity": round(link.title_similarity, 4),
                "alignment_ordinal": proposal.ordinal,
                "alignment_ordinal_delta": link.ordinal_delta,
                "alignment_target_public_id": hadith.public_id,
            }
        )
        claimed_hadith_ids.add(hadith.id)
        linked += 1
    return linked


def index_mirat_al_uqul(db: Session) -> CommentaryIndexStats:
    """Rebuild the full commentary index from previously crawled eShia pages."""
    commentary_book = db.execute(
        select(Book).where(Book.source_book_id == MIRAT_AL_UQUL_SOURCE_BOOK_ID)
    ).scalar_one_or_none()
    if commentary_book is None:
        raise ValueError("Mir'at al-'Uqul has not been crawled yet (eShia book 71429).")
    kafi_book = db.execute(
        select(Book).where(Book.source_book_id == AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID)
    ).scalar_one_or_none()
    if kafi_book is None:
        raise ValueError("The local al-Kafi corpus is required before commentary matching.")
    clear_hadith_token_cache()

    pages = (
        db.execute(
            select(Page)
            .where(Page.book_id == commentary_book.id)
            .order_by(Page.volume_number, Page.page_number)
        ).scalars().yield_per(50)
    )
    passages, reports, stats = extract_mirat_passages(pages, pages_are_ordered=True)
    hadiths = list(
        db.execute(
            select(Hadith)
            .where(
                Hadith.book_id == kafi_book.id,
                Hadith.review_status != "rejected_non_hadith_fragment",
            )
            .order_by(Hadith.sequence_in_book)
        ).scalars()
    )
    by_section_number = _local_section_index(hadiths)
    word_index = _hadith_word_index(hadiths)
    hadith_by_id = {hadith.id: hadith for hadith in hadiths}

    db.query(HadithCommentary).filter(
        HadithCommentary.commentary_book_id == commentary_book.id,
        HadithCommentary.source_key == MIRAT_AL_UQUL_SOURCE_KEY,
    ).delete(synchronize_session=False)

    claimed_hadith_ids: set[int] = set()
    decisions: list[_PassageDecision] = []
    for passage in passages:
        section_key = normalise_arabic_persian(passage.section_title or "")
        report = reports.get(
            report_key(passage.section_title, passage.section_occurrence, passage.printed_number or -1)
        )
        direct = by_section_number.get((section_key, passage.printed_number or -1), [])
        hadith: Hadith | None = None
        match_score: float | None = None
        match_method = "unmatched"
        match_status = "unmatched"
        evidence: dict = {
            "section_title_source": passage.section_title,
            "printed_number_source": passage.printed_number,
            "report_available": report is not None,
        }

        if len(direct) == 1:
            candidate = direct[0]
            score = _score_report(report, candidate)
            evidence["candidate_public_id"] = candidate.public_id
            evidence["report_match_score"] = score
            if score is not None and score >= 0.94:
                hadith = candidate
                match_score = score
                match_method = "section_number_and_text"
                match_status = "matched"
            else:
                text_candidate, text_score, runner_up = _best_text_candidate(
                    report, word_index, hadith_by_id
                )
                evidence["text_runner_up_score"] = runner_up
                if text_candidate is not None:
                    evidence["text_candidate_public_id"] = text_candidate.public_id
                    evidence["text_candidate_score"] = text_score
                same_section = text_candidate is not None and (
                    normalise_arabic_persian(text_candidate.section_title or "") == section_key
                )
                if (
                    same_section
                    and text_score is not None
                    and text_score >= 0.9
                    and (runner_up is None or text_score - runner_up >= 0.05)
                ):
                    hadith = text_candidate
                    match_score = text_score
                    match_method = "section_and_text_realigned"
                    match_status = "matched"
                else:
                    hadith = candidate
                    match_score = score
                    match_method = "section_number_only"
                    match_status = "needs_review"
        else:
            candidate, score, runner_up = _best_text_candidate(report, word_index, hadith_by_id)
            evidence["text_runner_up_score"] = runner_up
            if candidate is not None:
                evidence["candidate_public_id"] = candidate.public_id
                evidence["report_match_score"] = score
                if score is not None and score >= 0.985 and (runner_up is None or score - runner_up >= 0.05):
                    hadith = candidate
                    match_score = score
                    match_method = "text_only"
                    match_status = "matched"
                else:
                    hadith = candidate
                    match_score = score
                    match_method = "text_only"
                    match_status = "needs_review"

        if passage.printed_number is None:
            match_status = "malformed"
            match_method = "unreadable_header"
            hadith = None
            match_score = None

        # Review rows retain their candidate in the evidence only. This keeps
        # the public relationship one-to-one and avoids presenting ambiguity
        # as a second commentary for the same local hadith.
        if match_status != "matched":
            hadith = None
        elif hadith is not None and hadith.id in claimed_hadith_ids:
            evidence["duplicate_candidate_public_id"] = hadith.public_id
            hadith = None
            match_score = None
            match_method = "duplicate_candidate"
            match_status = "needs_review"
        elif hadith is not None:
            claimed_hadith_ids.add(hadith.id)

        decisions.append(
            _PassageDecision(
                passage=passage,
                report=report,
                hadith=hadith,
                match_status=match_status,
                match_method=match_method,
                match_score=match_score,
                evidence=evidence,
            )
        )

    # Second pass: place the passages al-Majlisi commented on without
    # reprinting. Text matching cannot reach them; position can.
    align_unquoted_passages(decisions, hadiths, claimed_hadith_ids)

    for decision in decisions:
        if decision.match_status == "matched":
            stats.matched += 1
        elif decision.match_status == "needs_review":
            stats.needs_review += 1
        elif decision.match_status == "malformed":
            stats.malformed += 1
        else:
            stats.unmatched += 1
        if decision.match_method == "chapter_sequence_aligned":
            stats.aligned += 1

        passage = decision.passage
        report = decision.report
        db.add(
            HadithCommentary(
                commentary_book_id=commentary_book.id,
                hadith_id=decision.hadith.id if decision.hadith is not None else None,
                source_key=MIRAT_AL_UQUL_SOURCE_KEY,
                source_sequence=passage.source_sequence,
                source_label=passage.source_label,
                section_title=passage.section_title,
                report_raw=report.text if report is not None else None,
                report_normalised=normalise_arabic_persian(report.text) if report is not None else None,
                commentary_raw=passage.text,
                commentary_normalised=normalise_arabic_persian(passage.text),
                volume_start=passage.volume_start,
                volume_end=passage.volume_end,
                page_start=passage.page_start,
                page_end=passage.page_end,
                source_url=_source_url(commentary_book, passage),
                match_status=decision.match_status,
                match_method=decision.match_method,
                match_score=decision.match_score,
                matcher_version=MIRAT_AL_UQUL_MATCHER_VERSION,
                match_evidence_json=decision.evidence,
            )
        )
    db.commit()
    return stats
