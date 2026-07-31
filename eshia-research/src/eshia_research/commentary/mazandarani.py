"""Extract al-Mazandarani's *Sharh Usul al-Kafi* from the eShia edition (13033).

Nothing from the Mir'at extractor transfers. That edition prints the report and
the sharh in distinct markup (`p` vs `span.FootNote`); this one has no markup at
all inside the content cell — bare text nodes separated by `<br>`. It is *sharh
mazji*: al-Kafi's words are quoted lemma by lemma in parentheses inside
continuous prose.

What makes it tractable is that the edition still names its layers in the text:

    باب صفة العلم وفضله وفضل العلماء     <- chapter
    * الأصل: 1 - محمد بن الحسن … قال …   <- al-Kafi report, numbered within the باب
      الشرح: (وجاهل مدع للعلم) من المفتريات …   <- al-Mazandarani
      … كما في (1) …      1 - كأنه أراد …       <- al-Sha'rani's gloss

Because the report's number is its position inside the باب — the same ordinal
al-Kafi's ``printed_number`` carries — the generic ``alignment`` engine applies
unchanged. Only this reader is new.

The gloss layer has **no delimiter in the markup**, so it is separated by
resolving its `(N)` references to `N -` markers. Where that fails the unit is
marked uncertain rather than published, because printing al-Sha'rani's words
under al-Mazandarani's name is a false attribution, not a formatting slip.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from eshia_research.commentary.alignment import (
    ChapterRun,
    align_chapters,
    propose_by_ordinal,
)
from eshia_research.commentary.matching import (
    best_text_candidate,
    clear_hadith_token_cache,
    comparable_tokens,
    hadith_word_index,
    score_report_text,
)
from eshia_research.commentary.sources import SHARH_AL_MAZANDARANI
from eshia_research.corpus import AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID
from eshia_research.models import Book, Hadith, HadithCommentary, Page
from eshia_research.normalise import normalise_arabic_persian

MAZANDARANI_SOURCE = SHARH_AL_MAZANDARANI

# The edition's own layer names. Volumes disagree about punctuation: most write
# «* الأصل: 1 - …», volume 8 writes «* الأصل 1 - …» with no colon at all — which
# is why requiring one found nothing in its 417 pages. A marker must therefore
# carry the asterisk *or* the colon; «الأصل» and «الشرح» are also ordinary words
# in the commentator's prose, and bare occurrences must not open a unit.
_BASE_MARKER = re.compile(r"(?:\*\s*الأصل\s*:?|الأصل\s*:)\s*")
_SHARH_MARKER = re.compile(r"(?:\*\s*الشرح\s*:?|الشرح\s*:)\s*")
_ORDINAL_PREFIX = re.compile(r"^\s*(?P<number>[0-9٠-٩۰-۹]+)\s*[-ـ–—]\s*")
_GLOSS_REFERENCE = re.compile(r"\((\d{1,2})\)")
_CHAPTER_LINE = re.compile(r"^(?:باب|كتاب)\s+\S+")
_WS = re.compile(r"\s+")


def _clean(value: str) -> str:
    return _WS.sub(" ", value).strip()


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    table = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    try:
        return int(value.translate(table))
    except ValueError:
        return None


@dataclass
class PageText:
    volume: int
    page: int
    body: str
    """The page's own text, with the gloss run removed."""

    gloss: str
    """al-Sha'rani's numbered notes, kept apart. Never merged into the sharh."""

    gloss_uncertain: bool
    """True when `(N)` references exist but could not be resolved in order."""

    chapter_title: str | None = None
    """Set only when this page *opens* with a chapter heading."""


@dataclass
class MazandaraniUnit:
    """One report and the commentary on it."""

    source_sequence: int
    section_title: str | None
    section_occurrence: int
    printed_number: int | None
    report: str
    commentary: str
    gloss: str
    gloss_uncertain: bool
    volume_start: int
    volume_end: int
    page_start: int
    page_end: int

    @property
    def publishable(self) -> bool:
        """Whether this unit may be published at all.

        Two requirements, and only two: the commentary must be al-Mazandarani's
        (the gloss was separated cleanly), and there must be commentary to show.

        Deliberately **not** requiring a printed number. An ordinal is what
        places a unit *by position*; it is not needed to identify one *by text*.
        Requiring it here excluded 263 units that carry both a commentary and a
        usable report from ever being matched, for want of a number the edition
        simply omitted.
        """
        return not self.gloss_uncertain and bool(self.commentary.strip())


def page_body(page: Page) -> str | None:
    """The reading text of one page, or None when the page carries no content."""
    if not page.html_raw:
        return None
    soup = BeautifulSoup(page.html_raw, "lxml")
    cell = soup.find("td", class_="book-page-show")
    if cell is None:
        return None
    menu = cell.find("div", class_="sticky-menue")
    if menu is not None:
        menu.extract()
    return _clean(cell.get_text(" ", strip=True))


def split_gloss(text: str) -> tuple[str, str, bool]:
    """Separate al-Sha'rani's numbered notes from al-Mazandarani's commentary.

    Returns ``(body, gloss, uncertain)``. The notes are recognised only by
    resolving the page's own `(N)` references to `N -` markers in ascending
    order, and only *after* the last reference — searching the whole page finds
    digit-dash pairs inside the prose and would cut the commentary in half.
    """
    references = sorted({int(m.group(1)) for m in _GLOSS_REFERENCE.finditer(text)})
    if not references:
        return text, "", False
    last_reference_end = max(m.end() for m in _GLOSS_REFERENCE.finditer(text))

    cursor = last_reference_end
    first_marker: int | None = None
    for number in references:
        marker = re.compile(r"(?<![0-9٠-٩])" + str(number) + r"\s*[-ـ–—]\s*")
        found = marker.search(text, cursor)
        if found is None:
            # A reference with no note after it: the run may continue onto the
            # next page, or the numbering is not what we assume. Either way the
            # boundary is unknown, so say so instead of guessing.
            return text, "", True
        if first_marker is None:
            first_marker = found.start()
        cursor = found.end()

    if first_marker is None:
        return text, "", True
    return _clean(text[:first_marker]), _clean(text[first_marker:]), False


def read_pages(pages: Iterable[Page]) -> list[PageText]:
    """Page texts in printed order, each already split from its gloss run."""
    ordered = sorted(
        (page for page in pages if page.volume_number is not None),
        key=lambda page: (page.volume_number or 0, page.page_number),
    )
    read: list[PageText] = []
    for page in ordered:
        body = page_body(page)
        if not body:
            continue
        text, gloss, uncertain = split_gloss(body)
        read.append(
            PageText(
                volume=page.volume_number or 0,
                page=page.page_number,
                body=text,
                gloss=gloss,
                gloss_uncertain=uncertain,
                chapter_title=opening_chapter_title(text),
            )
        )
    return read


_MAX_TITLE_LENGTH = 120


def opening_chapter_title(body: str) -> str | None:
    """The chapter heading a page opens with, if it opens with one.

    A heading is only trusted at the head of a page, because that is where this
    edition prints it. «باب» and «كتاب» are ordinary words that recur constantly
    inside al-Mazandarani's prose («كتاب والسنة، إذ بهما يتوصل …»), so scanning
    the whole text for them invents chapters out of sentences — which fragmented
    volume 2 into 111 runs where it has about 23.

    The edition also prints a truncated running header before the full title
    («باب صفة العلم  باب صفة العلم وفضله وفضل العلماء»), so among the headings in
    that opening stretch the longest is the complete one.
    """
    text = _clean(body)
    if not _CHAPTER_LINE.match(text):
        return None
    lead = _BASE_MARKER.split(text, maxsplit=1)[0]
    # Where a chapter opens with no «الأصل» on the same page, the commentary
    # runs straight on from the heading — «كتاب فرض العلم (ووجوب طلبه) العطف
    # للتفسير …». Its first parenthesised lemma marks where the title ended, and
    # a title that swallows commentary destroys the title agreement the
    # alignment layer needs to pair the chapter.
    lead = lead.split("(", 1)[0]
    candidates = [
        _clean(part)
        for part in re.split(r"(?=(?:باب|كتاب)\s)", lead)
        if _CHAPTER_LINE.match(_clean(part))
    ]
    candidates = [c for c in candidates if len(c) <= _MAX_TITLE_LENGTH]
    if not candidates:
        return None
    return max(candidates, key=len)


_REPORT_NUMBER_RE = re.compile(r"(?<![0-9٠-٩۰-۹])([0-9٠-٩۰-۹]{1,3})\s*[-ـ–—]\s*")
_ISNAD_HINT_RE = re.compile(r"\bعن\b|\bقال\b")
_ISNAD_LOOKAHEAD = 90


def unit_starts(stream: str) -> list[tuple[int, int]]:
    """Where each (report, commentary) unit begins: ``(start, text_start)``.

    The edition is not consistent about how it opens a report. Most volumes
    write «* الأصل: 30 - محمد بن يحيى …»; volume 9 drops «الأصل» entirely and
    opens with the bare number, «… 30 - محمد بن يحيى …», which is why keying on
    «الأصل» alone found 4 units in its 438 pages.

    So a unit opens at an «الأصل:» marker, or — once we are already inside a
    commentary — at a numbered report. The commentary requirement matters: a
    numbered run inside a *report* is part of that report, not a new one. The
    isnad hint is a second guard, since a chain almost always says «عن» or
    «قال» within a few words of its opening.
    """
    events: list[tuple[int, str, int]] = []
    for match in _BASE_MARKER.finditer(stream):
        events.append((match.start(), "base", match.end()))
    for match in _SHARH_MARKER.finditer(stream):
        events.append((match.start(), "sharh", match.end()))
    for match in _REPORT_NUMBER_RE.finditer(stream):
        events.append((match.start(), "number", match.start()))
    events.sort(key=lambda item: (item[0], {"base": 0, "sharh": 1, "number": 2}[item[1]]))

    starts: list[tuple[int, int]] = []
    in_commentary = False
    for position, kind, text_start in events:
        if kind == "base":
            starts.append((position, text_start))
            in_commentary = False
        elif kind == "sharh":
            in_commentary = True
        elif in_commentary:
            window = stream[position:position + _ISNAD_LOOKAHEAD]
            if _ISNAD_HINT_RE.search(window):
                starts.append((position, position))
                in_commentary = False
    return starts


def extract_units(pages: Iterable[Page]) -> list[MazandaraniUnit]:
    """Split the edition into (report, commentary) units in printed order."""
    read = read_pages(pages)
    if not read:
        return []

    # One stream, with an index back to the page every character came from, so
    # a unit spanning a page break still reports its true printed extent.
    stream_parts: list[str] = []
    owners: list[PageText] = []
    for entry in read:
        if stream_parts:
            stream_parts.append(" ")
            owners.append(entry)
        start = len("".join(stream_parts))
        stream_parts.append(entry.body)
        owners.extend([entry] * (len("".join(stream_parts)) - start))
    stream = "".join(stream_parts)

    def owner_at(index: int) -> PageText:
        return owners[min(max(index, 0), len(owners) - 1)]

    units: list[MazandaraniUnit] = []
    current_section: str | None = None
    current_key: str | None = None
    occurrence = 0

    # Chapter openings, located in the stream by the page that carries them.
    # Only page-leading headings count (see opening_chapter_title).
    openings: list[tuple[int, str]] = []
    for index, entry in enumerate(owners):
        if index and owners[index - 1] is entry:
            continue
        if entry.chapter_title:
            openings.append((index, entry.chapter_title))

    starts = unit_starts(stream)
    for position, (start, skip_to) in enumerate(starts):
        for opening_index, heading in openings:
            if opening_index > start:
                break
            key = normalise_arabic_persian(heading)
            if key != current_key:
                current_key = key
                occurrence += 1
            current_section = heading
        openings = [item for item in openings if item[0] > start]

        end = starts[position + 1][0] if position + 1 < len(starts) else len(stream)
        block = stream[skip_to:end]

        ordinal_match = _ORDINAL_PREFIX.match(block)
        number = _to_int(ordinal_match.group("number")) if ordinal_match else None
        remainder = block[ordinal_match.end():] if ordinal_match else block

        sharh = _SHARH_MARKER.search(remainder)
        if sharh is not None:
            report = _clean(remainder[: sharh.start()])
            commentary = _clean(remainder[sharh.end():])
        else:
            # No sharh marker: the whole block is base text (the commentator
            # passed over this report, or it runs on to the next page).
            report = _clean(remainder)
            commentary = ""

        head, tail = owner_at(start), owner_at(max(end - 1, 0))
        spanned = read[read.index(head): read.index(tail) + 1]
        units.append(
            MazandaraniUnit(
                source_sequence=len(units) + 1,
                section_title=current_section,
                section_occurrence=max(occurrence, 1),
                printed_number=number,
                report=report,
                commentary=commentary,
                gloss=_clean(" ".join(p.gloss for p in spanned if p.gloss)),
                gloss_uncertain=any(p.gloss_uncertain for p in spanned),
                volume_start=head.volume,
                volume_end=tail.volume,
                page_start=head.page,
                page_end=tail.page,
            )
        )
    fill_missing_ordinals(units)
    return units


def fill_missing_ordinals(units: list[MazandaraniUnit]) -> int:
    """Number the reports whose printed number the edition omitted.

    Volumes 7, 10 and 12 print «الأصل: - علي بن إبراهيم …» — the dash but no
    number — for a few hundred reports. Reports appear in order inside a chapter,
    so a gap between two numbered neighbours is arithmetic rather than guesswork:
    between 4 and 6 the missing one is 5. Anything that does not add up exactly
    is left unnumbered, because a wrong ordinal would attach the commentary to
    the neighbouring hadith.
    """
    runs: dict[int, list[MazandaraniUnit]] = {}
    for unit in units:
        runs.setdefault(unit.section_occurrence, []).append(unit)

    filled = 0
    for members in runs.values():
        numbered = [i for i, u in enumerate(members) if u.printed_number is not None]
        for index, unit in enumerate(members):
            if unit.printed_number is not None:
                continue
            before = [i for i in numbered if i < index]
            after = [i for i in numbered if i > index]
            if before and after:
                lo, hi = before[-1], after[0]
                low, high = members[lo].printed_number, members[hi].printed_number
                if low is not None and high is not None and high - low == hi - lo:
                    unit.printed_number = low + (index - lo)
                    filled += 1
            elif after:
                # Leading gap: count back from the first numbered report.
                first = after[0]
                value = members[first].printed_number
                if value is not None and value - (first - index) >= 1:
                    unit.printed_number = value - (first - index)
                    filled += 1
    return filled


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

# Sharh Usul al-Kafi covers the Usul and the Rawda, and nothing else. Coverage
# reported against the whole of al-Kafi would read as failure on five volumes
# the work never set out to explain.
MAZANDARANI_TARGET_VOLUMES = (1, 2, 8)

_TEXT_ONLY_THRESHOLD = 0.985
_RUNNER_UP_GAP = 0.05
# Text alone must clear 0.985 because that bar exists to separate near-ties.
# When a *second, independent* witness agrees — the identified hadith carries
# the same number inside its chapter as this unit does — the ambiguity the high
# bar guards against is not present, and a lower score is enough. This is the
# same two-evidence rule Mir'at uses for `section_number_and_text`; it is not a
# relaxed threshold but a different, stronger evidential position.
_CORROBORATED_THRESHOLD = 0.90
_MIN_ANCHOR_SUPPORT = 2
_MIN_TITLE_SIMILARITY = 0.6
_MIN_DELTA_AGREEMENT = 0.8
_CONTRADICTION_SCORE = 0.35


@dataclass
class MazandaraniIndexStats:
    pages_seen: int = 0
    units: int = 0
    publishable: int = 0
    matched: int = 0
    aligned: int = 0
    needs_review: int = 0
    unmatched: int = 0
    withheld_attribution: int = 0
    """Units held back because the gloss could not be separated from the sharh."""

    no_commentary_in_source: int = 0
    """Reports the commentator passed over. Not a defect — he comments on
    groups, printing several reports and explaining once, so these will never
    yield a link and must not be counted as missing coverage."""

    target_hadiths: int = 0
    """Hadiths in the covered part of al-Kafi — the honest denominator."""


@dataclass
class _UnitDecision:
    unit: MazandaraniUnit
    hadith: Hadith | None
    match_status: str
    match_method: str
    match_score: float | None
    evidence: dict


def target_hadiths(db: Session, kafi_book_id: int) -> list[Hadith]:
    """The al-Kafi hadiths this sharh actually addresses, in printed order."""
    return list(
        db.execute(
            select(Hadith)
            .where(
                Hadith.book_id == kafi_book_id,
                Hadith.review_status != "rejected_non_hadith_fragment",
                Hadith.volume_start.in_(MAZANDARANI_TARGET_VOLUMES),
            )
            .order_by(Hadith.sequence_in_book)
        ).scalars()
    )


def build_target_runs(hadiths: list[Hadith]) -> list[ChapterRun]:
    """Split the covered al-Kafi into numbered chapter runs, in printed order."""
    runs: list[ChapterRun] = []
    previous_title: object = object()
    last_ordinal: int | None = None
    for hadith in hadiths:
        title = hadith.section_title or ""
        ordinal = _to_int(hadith.printed_number)
        restarted = ordinal is not None and last_ordinal is not None and ordinal <= last_ordinal
        if title != previous_title or restarted:
            runs.append(ChapterRun(index=len(runs), title=title))
            previous_title = title
            last_ordinal = None
        if ordinal is not None:
            runs[-1].units_by_ordinal.setdefault(ordinal, hadith)
            last_ordinal = ordinal
    return runs


def build_source_runs(units: list[MazandaraniUnit]) -> list[ChapterRun]:
    """Group the sharh into numbered chapter runs, in printed order.

    A run ends where the heading changes **or the numbering restarts** — the
    same rule the al-Kafi side uses. Grouping by heading alone merged chapters
    whose heading the edition did not mark, so their numbering read `1..6,1..5`
    and every unit whose ordinal was already taken fell out of the run entirely.
    Those units then had no position, and position is the only thing that can
    place a report al-Kafi prints more than once.
    """
    runs: list[ChapterRun] = []
    previous_occurrence: object = object()
    last_ordinal: int | None = None
    for unit in units:
        if unit.printed_number is None:
            continue
        restarted = last_ordinal is not None and unit.printed_number <= last_ordinal
        if unit.section_occurrence != previous_occurrence or restarted:
            runs.append(ChapterRun(index=len(runs), title=unit.section_title or ""))
            previous_occurrence = unit.section_occurrence
        runs[-1].units_by_ordinal.setdefault(unit.printed_number, unit)
        last_ordinal = unit.printed_number
    return runs


def _source_url(book: Book, unit: MazandaraniUnit) -> str:
    base = book.source_url.rstrip("/")
    if re.search(r"/\d+(/\d+)?$", base):
        base = re.sub(r"/\d+(/\d+)?$", "", base)
    return f"{base}/{unit.volume_start}/{unit.page_start}"


def index_sharh_al_mazandarani(db: Session) -> MazandaraniIndexStats:
    """Index the sharh against the Usul and Rawda of the local al-Kafi."""
    source = SHARH_AL_MAZANDARANI
    commentary_book = db.execute(
        select(Book).where(Book.source_book_id == source.source_book_id)
    ).scalar_one_or_none()
    if commentary_book is None:
        raise ValueError(
            f"{source.title_en} has not been crawled yet (eShia {source.source_book_id})."
        )
    kafi_book = db.execute(
        select(Book).where(Book.source_book_id == AL_KAFI_ISLAMIYYA_SOURCE_BOOK_ID)
    ).scalar_one_or_none()
    if kafi_book is None:
        raise ValueError("The local al-Kafi corpus is required before commentary matching.")
    clear_hadith_token_cache()

    pages = list(
        db.execute(
            select(Page).where(Page.book_id == commentary_book.id)
            .order_by(Page.volume_number, Page.page_number)
        ).scalars()
    )
    stats = MazandaraniIndexStats(pages_seen=len(pages))
    units = extract_units(pages)
    stats.units = len(units)
    stats.publishable = sum(1 for unit in units if unit.publishable)
    stats.withheld_attribution = sum(1 for unit in units if unit.gloss_uncertain)
    stats.no_commentary_in_source = sum(
        1 for unit in units if not unit.gloss_uncertain and not unit.commentary.strip()
    )

    hadiths = target_hadiths(db, kafi_book.id)
    stats.target_hadiths = len(hadiths)
    word_index = hadith_word_index(hadiths)
    hadith_by_id = {hadith.id: hadith for hadith in hadiths}

    db.query(HadithCommentary).filter(
        HadithCommentary.commentary_book_id == commentary_book.id,
        HadithCommentary.source_key == source.key,
    ).delete(synchronize_session=False)

    claimed: set[int] = set()
    decisions: list[_UnitDecision] = []
    for unit in units:
        evidence: dict = {
            "section_title_source": unit.section_title,
            "printed_number_source": unit.printed_number,
            "gloss_separated_chars": len(unit.gloss),
            "gloss_uncertain": unit.gloss_uncertain,
        }
        hadith: Hadith | None = None
        score: float | None = None
        method = "unmatched"
        status = "unmatched"

        if not unit.publishable:
            # Nothing to publish. Distinguish the two reasons, because they mean
            # opposite things: an attribution we could not establish is a defect
            # to chase, whereas a report the commentator passed over in silence
            # is the work itself and will never yield a link. Al-Mazandarani
            # regularly prints several reports in a row and comments once, so a
            # report with no sharh is normal, not a parser failure.
            method = (
                "withheld_attribution" if unit.gloss_uncertain else "no_commentary_in_source"
            )
            status = "needs_review"
        else:
            candidate, candidate_score, runner_up = best_text_candidate(
                unit.report, word_index, hadith_by_id
            )
            evidence["text_runner_up_score"] = runner_up
            if candidate is not None:
                evidence["candidate_public_id"] = candidate.public_id
                evidence["report_match_score"] = candidate_score
                confident = (
                    candidate_score is not None
                    and candidate_score >= _TEXT_ONLY_THRESHOLD
                    and (runner_up is None or candidate_score - runner_up >= _RUNNER_UP_GAP)
                )
                same_ordinal = (
                    unit.printed_number is not None
                    and _to_int(candidate.printed_number) == unit.printed_number
                )
                corroborated = (
                    not confident
                    and candidate_score is not None
                    and candidate_score >= _CORROBORATED_THRESHOLD
                    and same_ordinal
                )
                evidence["ordinal_corroborates"] = same_ordinal
                hadith = candidate if (confident or corroborated) else None
                score = candidate_score
                method = "text_and_ordinal" if corroborated else "text_only"
                status = "matched" if hadith is not None else "needs_review"

        if status != "matched":
            hadith = None

        decisions.append(_UnitDecision(unit, hadith, status, method, score, evidence))

    claimed = _settle_contention(decisions)
    _align_unquoted_units(decisions, hadiths, claimed)

    for decision in decisions:
        unit = decision.unit
        if decision.match_status == "matched":
            stats.matched += 1
        elif decision.match_status == "needs_review":
            stats.needs_review += 1
        else:
            stats.unmatched += 1
        if decision.match_method == "chapter_sequence_aligned":
            stats.aligned += 1
        db.add(
            HadithCommentary(
                commentary_book_id=commentary_book.id,
                hadith_id=decision.hadith.id if decision.hadith is not None else None,
                source_key=source.key,
                source_sequence=unit.source_sequence,
                source_label=(
                    f"الأصل {unit.printed_number}" if unit.printed_number else None
                ),
                section_title=unit.section_title,
                report_raw=unit.report or None,
                report_normalised=(
                    normalise_arabic_persian(unit.report) if unit.report else None
                ),
                # The gloss belongs to al-Sha'rani, so it is never part of what
                # is published as al-Mazandarani's commentary.
                commentary_raw=unit.commentary,
                commentary_normalised=normalise_arabic_persian(unit.commentary),
                volume_start=unit.volume_start,
                volume_end=unit.volume_end,
                page_start=unit.page_start,
                page_end=unit.page_end,
                source_url=_source_url(commentary_book, unit),
                match_status=decision.match_status,
                match_method=decision.match_method,
                match_score=decision.match_score,
                matcher_version=source.matcher_version,
                match_evidence_json=decision.evidence,
            )
        )
    db.commit()
    return stats


def _settle_contention(decisions: list[_UnitDecision]) -> set[int]:
    """Award a contested hadith to the best-evidenced claimant, not the first.

    Several units can identify the same hadith — al-Kafi prints some reports
    more than once, and the commentator quotes a report again when he returns to
    it. Awarding on iteration order is arbitrary, and it is exactly how Mir'at
    published 729 wrong links before the carry-over fix. Rank instead:
    corroborated evidence beats uncorroborated, then the higher text score, then
    the fuller quote. Losers drop back to review, where alignment may still
    place them somewhere else.
    """
    by_target: dict[int, list[_UnitDecision]] = {}
    for decision in decisions:
        if decision.match_status == "matched" and decision.hadith is not None:
            by_target.setdefault(decision.hadith.id, []).append(decision)

    def strength(decision: _UnitDecision) -> tuple[int, float, int]:
        corroborated = decision.match_method == "text_and_ordinal"
        return (
            1 if corroborated else 0,
            decision.match_score or 0.0,
            len(decision.unit.report or ""),
        )

    claimed: set[int] = set()
    for hadith_id, contenders in by_target.items():
        contenders.sort(key=strength, reverse=True)
        winner, losers = contenders[0], contenders[1:]
        claimed.add(hadith_id)
        for loser in losers:
            loser.evidence["duplicate_candidate_public_id"] = loser.hadith.public_id
            loser.evidence["lost_to_source_sequence"] = winner.unit.source_sequence
            loser.evidence["lost_to_score"] = winner.match_score
            loser.hadith = None
            loser.match_score = None
            loser.match_method = "duplicate_candidate"
            loser.match_status = "needs_review"
    return claimed


def _align_unquoted_units(
    decisions: list[_UnitDecision],
    hadiths: list[Hadith],
    claimed: set[int],
) -> int:
    """Place by chapter position what the text could not place. See alignment.py."""
    units = [decision.unit for decision in decisions]
    source_runs = build_source_runs(units)
    target_runs = build_target_runs(hadiths)
    if not source_runs or not target_runs:
        return 0

    position_by_hadith_id: dict[int, tuple[int, int]] = {}
    for run in target_runs:
        for ordinal, hadith in run.units_by_ordinal.items():
            position_by_hadith_id[hadith.id] = (run.index, ordinal)

    by_sequence = {d.unit.source_sequence: d for d in decisions}
    confirmed: dict[int, tuple[int, int]] = {}
    for decision in decisions:
        if decision.match_status == "matched" and decision.hadith is not None:
            position = position_by_hadith_id.get(decision.hadith.id)
            if position is not None:
                confirmed[decision.unit.source_sequence] = position

    links = align_chapters(
        source_runs,
        target_runs,
        confirmed,
        lambda unit: unit.source_sequence,
        source_titles=[comparable_tokens(run.title) for run in source_runs],
        target_titles=[comparable_tokens(run.title) for run in target_runs],
    )

    linked = 0
    for proposal in propose_by_ordinal(source_runs, target_runs, links):
        decision = by_sequence.get(proposal.source_unit.source_sequence)
        if decision is None or decision.match_status == "matched":
            continue
        if not decision.unit.publishable:
            continue
        hadith = proposal.target_unit
        if hadith.id in claimed:
            continue
        link = proposal.link
        trustworthy = (
            link.anchor_support >= _MIN_ANCHOR_SUPPORT
            or (link.anchor_support >= 1 and link.title_similarity >= _MIN_TITLE_SIMILARITY)
            or (link.method == "interpolated" and link.title_similarity >= _MIN_TITLE_SIMILARITY)
        )
        if not trustworthy or link.ordinal_delta_confidence < _MIN_DELTA_AGREEMENT:
            continue
        contradiction = score_report_text(decision.unit.report, hadith)
        if contradiction is not None and contradiction < _CONTRADICTION_SCORE:
            decision.evidence["alignment_rejected_public_id"] = hadith.public_id
            decision.evidence["alignment_contradiction_score"] = contradiction
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
        claimed.add(hadith.id)
        linked += 1
    return linked
