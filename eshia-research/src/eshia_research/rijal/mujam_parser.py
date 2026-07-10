"""Parser for al-Khu'i's Mu'jam Rijal al-Hadith pages.

The important constraint is that a printed ``123- name:`` pattern is not
always a narrator entry. Mu'jam sometimes contains numbered lists inside a
long entry, and an eShia page can begin in the middle of that list. The parser
therefore follows the main entry-number sequence and ignores local numbered
lists that reset to small numbers.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
import re

from eshia_research.normalise import normalise_arabic_persian

MUJAM_SOURCE_BOOK_ID = "14036"
MUJAM_ENTRY_START = (1, 107)
MUJAM_ENTRY_KIND = "mujam_numbered_entry"
MUJAM_PARSER_VERSION = "mujam_v1"
MAX_MAIN_ENTRY_NUMBER = 15800
MAX_ENTRY_NUMBER_GAP = 25


@dataclass(frozen=True)
class MujamPage:
    id: int
    volume_number: int
    page_number: int
    text_raw: str
    source_url: str | None = None


@dataclass(frozen=True)
class HeaderCandidate:
    entry_number: int
    title_raw: str
    page_id: int
    volume_number: int
    page_number: int
    source_url: str | None
    global_start: int
    match_end: int


@dataclass(frozen=True)
class ParsedStatement:
    source_name: str
    statement_type: str
    quote_raw: str
    evidence_text_raw: str | None = None
    metadata: dict | None = None
    confidence: int = 75


@dataclass(frozen=True)
class ParsedOccurrence:
    direction: str
    related_name_raw: str
    source_ref_raw: str | None
    evidence_text_raw: str
    metadata: dict | None = None
    confidence: int = 70


@dataclass(frozen=True)
class ParsedAlias:
    alias_raw: str
    alias_type: str
    source_note: str | None = None
    confidence: int = 80


@dataclass
class ParsedMujamEntry:
    entry_number: int
    title_raw: str
    canonical_name_raw: str
    page_start_id: int
    page_end_id: int
    volume_start: int
    page_start: int
    volume_end: int
    page_end: int
    source_url: str | None
    text_raw: str
    flags: set[str] = field(default_factory=set)
    aliases: list[ParsedAlias] = field(default_factory=list)
    statements: list[ParsedStatement] = field(default_factory=list)
    occurrences: list[ParsedOccurrence] = field(default_factory=list)

    @property
    def review_status(self) -> str:
        review_flags = {"short_entry", "title_unclosed_bracket"}
        return "needs_review" if self.flags & review_flags else "pending"


@dataclass(frozen=True)
class ParseStats:
    headers_seen: int
    headers_accepted: int
    headers_ignored: int
    sequence_gaps: int
    last_entry_number: int | None


_HEADER_RE = re.compile(r"(?m)^([0-9]{1,5})-\s+([^\n:]{1,180}):")
_WS_RE = re.compile(r"\s+")
_BRACKET_ALIAS_RE = re.compile(r"\[([^\[\]]{2,120})\]")
_SOURCE_REF_RE = re.compile(
    r"(?:الكافي|الفقيه|التهذيب|الإستبصار|الاستبصار):\s*[^.]{1,320}(?:\.|$)"
)
_IMAM_MARKER_RE = re.compile(r"\(\s*ع\s*\)")

_SOURCE_LABELS = {
    "الشيخ الحر": "hurr_al_amili",
    "ابن الغضائري": "ibn_al_ghadairi",
    "ابن داود": "ibn_dawud",
    "العلامة": "allama_hilli",
    "النجاشي": "najashi",
    "الشيخ": "tusi",
    "الكشي": "kashshi",
    "البرقي": "barqi",
    "الصدوق": "saduq",
}
_SOURCE_ALT = "|".join(re.escape(label) for label in sorted(_SOURCE_LABELS, key=len, reverse=True))
_QUOTED_STATEMENT_RE = re.compile(
    rf"(?P<verb>قال|ذكر|عده|روى)\s+(?P<label>{_SOURCE_ALT})(?P<prefix>[^«»]{{0,180}})"
    r"[:،]?\s*«(?P<quote>[^»]{2,5000})»"
)
_AQUL_RE = re.compile(r"أقول:\s*(?P<comment>.{20,1400}?)(?=(?:\n[0-9]{1,5}-\s)|$)", re.S)
_TABAQAH_RE = re.compile(
    r"(?P<quote>من أصحاب\s+(?P<imam>[^،.]{2,80})(?:\s*\(\s*ع\s*\))?[^.]{0,120}رجال الشيخ\s*\((?P<number>[0-9]+)\))"
)
_FROM_RE = re.compile(
    r"روى\s+عن\s+(?P<name>.{2,140}?)(?=،\s*و|\.|،\s*(?:الكافي|الفقيه|التهذيب|الإستبصار|الاستبصار):)",
    re.S,
)
_BY_RE = re.compile(
    r"روى\s+عنه\s+(?P<name>.{2,140}?)(?=،\s*و|\.|،\s*(?:الكافي|الفقيه|التهذيب|الإستبصار|الاستبصار):)",
    re.S,
)
_BY_COMPLEX_RE = re.compile(r"روى\s+(?P<name>.{2,140}?)\s+عنه(?=،\s*و|\.|،)", re.S)


def compact_text(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def canonical_name_from_title(title_raw: str) -> str:
    canonical = re.sub(r"\s*\[.*$", "", title_raw).strip()
    return compact_text(canonical.rstrip(":"))


def aliases_from_title(title_raw: str, canonical_name: str) -> list[ParsedAlias]:
    aliases: list[ParsedAlias] = []
    seen = {normalise_arabic_persian(canonical_name)}
    title_norm = normalise_arabic_persian(compact_text(title_raw))
    if title_norm and title_norm not in seen:
        aliases.append(
            ParsedAlias(
                alias_raw=compact_text(title_raw),
                alias_type="entry_title",
                source_note="Mu'jam entry title",
                confidence=90,
            )
        )
        seen.add(title_norm)
    for match in _BRACKET_ALIAS_RE.finditer(title_raw):
        alias = compact_text(match.group(1))
        alias_norm = normalise_arabic_persian(alias)
        if alias_norm and alias_norm not in seen:
            aliases.append(
                ParsedAlias(
                    alias_raw=alias,
                    alias_type="bracket_variant",
                    source_note="Bracketed Mu'jam title variant",
                    confidence=70,
                )
            )
            seen.add(alias_norm)
    return aliases


def iter_header_candidates(pages: list[MujamPage]) -> list[HeaderCandidate]:
    candidates: list[HeaderCandidate] = []
    offset = 0
    for page in sorted(pages, key=lambda p: (p.volume_number, p.page_number)):
        page_text = page.text_raw or ""
        if (page.volume_number, page.page_number) < MUJAM_ENTRY_START:
            offset += len(page_text) + 2
            continue
        for match in _HEADER_RE.finditer(page_text):
            candidates.append(
                HeaderCandidate(
                    entry_number=int(match.group(1)),
                    title_raw=compact_text(match.group(2)),
                    page_id=page.id,
                    volume_number=page.volume_number,
                    page_number=page.page_number,
                    source_url=page.source_url,
                    global_start=offset + match.start(),
                    match_end=offset + match.end(),
                )
            )
        offset += len(page_text) + 2
    return candidates


def select_main_headers(candidates: list[HeaderCandidate]) -> tuple[list[HeaderCandidate], ParseStats]:
    accepted: list[HeaderCandidate] = []
    previous = 0
    sequence_gaps = 0
    for candidate in candidates:
        number = candidate.entry_number
        if previous == 0:
            if number == 1:
                accepted.append(candidate)
                previous = number
            continue
        if number <= previous:
            continue
        if number > MAX_MAIN_ENTRY_NUMBER:
            continue
        if number - previous > MAX_ENTRY_NUMBER_GAP:
            continue
        if number != previous + 1:
            sequence_gaps += 1
        accepted.append(candidate)
        previous = number

    return accepted, ParseStats(
        headers_seen=len(candidates),
        headers_accepted=len(accepted),
        headers_ignored=len(candidates) - len(accepted),
        sequence_gaps=sequence_gaps,
        last_entry_number=accepted[-1].entry_number if accepted else None,
    )


def _page_spans(pages: list[MujamPage]) -> tuple[str, list[int], list[MujamPage]]:
    full_parts: list[str] = []
    starts: list[int] = []
    ordered = sorted(pages, key=lambda p: (p.volume_number, p.page_number))
    offset = 0
    for page in ordered:
        starts.append(offset)
        text = page.text_raw or ""
        full_parts.append(text)
        offset += len(text)
        full_parts.append("\n\n")
        offset += 2
    return "".join(full_parts), starts, ordered


def _page_for_offset(offset: int, starts: list[int], pages: list[MujamPage]) -> MujamPage:
    index = bisect_right(starts, offset) - 1
    return pages[max(0, min(index, len(pages) - 1))]


def _next_page_start(offset: int, starts: list[int], full_text_length: int) -> int:
    index = bisect_right(starts, offset) - 1
    if index + 1 < len(starts):
        return starts[index + 1]
    return full_text_length


def extract_statements(text_raw: str) -> list[ParsedStatement]:
    statements: list[ParsedStatement] = []
    for match in _QUOTED_STATEMENT_RE.finditer(text_raw):
        label = match.group("label")
        quote = compact_text(match.group("quote"))
        evidence = compact_text(match.group(0))
        statements.append(
            ParsedStatement(
                source_name=_SOURCE_LABELS[label],
                statement_type="quoted_statement",
                quote_raw=quote,
                evidence_text_raw=evidence,
                metadata={"label_raw": label, "verb": match.group("verb")},
                confidence=85,
            )
        )

    for match in _TABAQAH_RE.finditer(text_raw):
        statements.append(
            ParsedStatement(
                source_name="tusi_rijal",
                statement_type="tabaqah_membership",
                quote_raw=compact_text(match.group("quote")),
                evidence_text_raw=compact_text(match.group(0)),
                metadata={"imam_raw": compact_text(match.group("imam")), "rijal_tusi_number": match.group("number")},
                confidence=80,
            )
        )

    for match in _AQUL_RE.finditer(text_raw):
        statements.append(
            ParsedStatement(
                source_name="khui",
                statement_type="compiler_comment",
                quote_raw=compact_text(match.group("comment")),
                evidence_text_raw=compact_text(match.group(0)),
                confidence=70,
            )
        )
    return statements


def _clean_related_name(raw: str) -> str:
    name = _IMAM_MARKER_RE.sub(" ", raw)
    name = name.strip(" .،:؛")
    return compact_text(name)


def _source_ref_after(text: str, start: int) -> str | None:
    window = text[start : start + 650]
    match = _SOURCE_REF_RE.search(window)
    if match and re.search(r"\.\s*(?:و\s*)?روى\s+عن", window[: match.start()]):
        return None
    return compact_text(match.group(0)) if match else None


def extract_occurrences(text_raw: str) -> list[ParsedOccurrence]:
    occurrences: list[ParsedOccurrence] = []
    seen: set[tuple[str, str, str | None]] = set()
    patterns = (
        ("narrates_from", _FROM_RE),
        ("narrated_by", _BY_RE),
        ("narrated_by", _BY_COMPLEX_RE),
    )
    for direction, pattern in patterns:
        for match in pattern.finditer(text_raw):
            related = _clean_related_name(match.group("name"))
            if not related or len(related) > 512:
                continue
            if any(source in related for source in ("الكافي", "الفقيه", "التهذيب", "الإستبصار", "الاستبصار")):
                continue
            source_ref = _source_ref_after(text_raw, match.end())
            if source_ref is None:
                continue
            key = (direction, normalise_arabic_persian(related), source_ref)
            if key in seen:
                continue
            seen.add(key)
            evidence = compact_text(text_raw[match.start() : min(len(text_raw), match.end() + 220)])
            occurrences.append(
                ParsedOccurrence(
                    direction=direction,
                    related_name_raw=related,
                    source_ref_raw=source_ref,
                    evidence_text_raw=evidence,
                    confidence=75 if source_ref else 60,
                )
            )
    return occurrences


def parse_mujam_entries(pages: list[MujamPage]) -> tuple[list[ParsedMujamEntry], ParseStats]:
    if not pages:
        return [], ParseStats(0, 0, 0, 0, None)

    full_text, starts, ordered_pages = _page_spans(pages)
    candidates = iter_header_candidates(pages)
    headers, stats = select_main_headers(candidates)
    entries: list[ParsedMujamEntry] = []

    for index, header in enumerate(headers):
        if index + 1 < len(headers):
            next_start = headers[index + 1].global_start
        else:
            # The printed Mu'jam entries end before volume 24's trailing
            # blank/index pages. With no next header, cap the final entry at
            # its start page instead of swallowing the rest of the volume.
            next_start = _next_page_start(header.global_start, starts, len(full_text))
        entry_text = full_text[header.global_start : next_start].strip()
        start_page = _page_for_offset(header.global_start, starts, ordered_pages)
        end_page = _page_for_offset(max(header.global_start, next_start - 1), starts, ordered_pages)
        canonical_name = canonical_name_from_title(header.title_raw)
        flags: set[str] = set()
        if index and header.entry_number != headers[index - 1].entry_number + 1:
            flags.add("sequence_gap")
        if "[" in header.title_raw and "]" not in header.title_raw:
            flags.add("title_unclosed_bracket")
        if len(entry_text) < 25:
            flags.add("short_entry")

        entries.append(
            ParsedMujamEntry(
                entry_number=header.entry_number,
                title_raw=header.title_raw,
                canonical_name_raw=canonical_name,
                page_start_id=start_page.id,
                page_end_id=end_page.id,
                volume_start=start_page.volume_number,
                page_start=start_page.page_number,
                volume_end=end_page.volume_number,
                page_end=end_page.page_number,
                source_url=header.source_url,
                text_raw=entry_text,
                flags=flags,
                aliases=aliases_from_title(header.title_raw, canonical_name),
                statements=extract_statements(entry_text),
                occurrences=extract_occurrences(entry_text),
            )
        )

    return entries, stats
