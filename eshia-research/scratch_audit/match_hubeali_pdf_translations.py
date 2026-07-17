"""Match untranslated local Al-Kafi reports to HubeAli's source PDFs."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select

from eshia_research.db import SessionLocal
from eshia_research.models import Book, Hadith, HadithTranslation
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.text import clean_ws, sha256_text


PUBLIC_STATUSES = {"machine_verified", "human_reviewed", "published"}
ARABIC_WORD_RE = re.compile(r"[\u0600-\u06ff]{2,}")
HADITH_MARKER_RE = re.compile(r"(?m)^H\s*(\d{3,6})\s*[-–]\s*")
PAGE_NOISE_RE = re.compile(
    r"^(?:Al\s*Kafi Volume.*|www\.hubeali\.com.*|\d+ out of \d+.*|TABLE OF CONTENTS.*|H \d+\s*\.{3,}\s*\d+)$",
    re.IGNORECASE,
)
SOURCE_FOOTNOTE_RE = re.compile(
    r"^\d+\s+Al\s*Kafi\s*.*\bCh\s*\d+\s+H\s*\d+",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PdfText:
    volume: int
    position: int
    path: Path
    source_url: str
    text: str
    words: list[str]
    word_offsets: list[int]
    joined_words: str
    joined_word_starts: list[int]
    markers: list[re.Match[str]]
    compact_arabic: str
    compact_offsets: list[int]


def arabic_words(text: str) -> list[str]:
    return ARABIC_WORD_RE.findall(normalise_arabic_persian(text))


def compact_arabic_with_offsets(text: str) -> tuple[str, list[int]]:
    """Return Arabic letters without PDF layout whitespace and their offsets."""

    normalised = normalise_arabic_persian(text)
    letters: list[str] = []
    offsets: list[int] = []
    for index, char in enumerate(normalised):
        if "\u0621" <= char <= "\u06ff" and char != "ـ":
            letters.append(char)
            offsets.append(index)
    return "".join(letters), offsets


def load_pdf_texts(directory: Path) -> list[PdfText]:
    manifest_path = directory / "manifest.json"
    source_urls: dict[str, str] = {}
    if manifest_path.exists():
        for row in json.loads(manifest_path.read_text(encoding="utf-8")):
            source_urls[Path(str(row["text_path"])).name] = str(row["source_url"])
    output: list[PdfText] = []
    paths = (
        sorted(directory / name for name in source_urls)
        if source_urls
        else sorted(directory.glob("v??-*.pdf.txt"))
    )
    for path in paths:
        volume = int(path.name[1:3])
        position = int(path.name[4:6])
        text = path.read_text(encoding="utf-8")
        normalised = normalise_arabic_persian(text)
        compact_arabic, compact_offsets = compact_arabic_with_offsets(text)
        matches = list(ARABIC_WORD_RE.finditer(normalised))
        words = [match.group(0) for match in matches]
        starts: list[int] = []
        joined_parts: list[str] = []
        cursor = 0
        for word in words:
            starts.append(cursor)
            joined_parts.append(word)
            cursor += len(word) + 1
        output.append(
            PdfText(
                volume=volume,
                position=position,
                path=path,
                source_url=source_urls.get(path.name, ""),
                text=text,
                words=words,
                word_offsets=[match.start() for match in matches],
                joined_words=" ".join(joined_parts),
                joined_word_starts=starts,
                markers=list(HADITH_MARKER_RE.finditer(text)),
                compact_arabic=compact_arabic,
                compact_offsets=compact_offsets,
            )
        )
    return output


def find_phrase(pdf: PdfText, words: list[str]) -> tuple[int, int, str] | None:
    if not words or not pdf.words:
        return None
    matcher = difflib.SequenceMatcher(None, words[:240], pdf.words, autojunk=False)
    block = matcher.find_longest_match()
    if block.size < 4:
        return None
    return (
        block.size,
        pdf.word_offsets[block.b],
        " ".join(words[block.a : block.a + block.size]),
    )


def find_compact_phrase(pdf: PdfText, text: str) -> tuple[int, int, str] | None:
    compact, _ = compact_arabic_with_offsets(text)
    if not compact or not pdf.compact_arabic:
        return None
    matcher = difflib.SequenceMatcher(None, compact[:5000], pdf.compact_arabic, autojunk=False)
    block = matcher.find_longest_match()
    if block.size < 24:
        return None
    return (
        block.size,
        pdf.compact_offsets[block.b],
        compact[block.a : block.a + block.size],
    )


def longest_block_size(pdf: PdfText, words: list[str]) -> int:
    if not words:
        return 0
    return difflib.SequenceMatcher(None, words, pdf.words, autojunk=False).find_longest_match().size


def _rightmost_le(values: list[int], target: int) -> int:
    low, high = 0, len(values) - 1
    while low < high:
        middle = (low + high + 1) // 2
        if values[middle] <= target:
            low = middle
        else:
            high = middle - 1
    return low


def following_marker(pdf: PdfText, offset: int) -> tuple[int, re.Match[str]] | None:
    for marker_index, marker in enumerate(pdf.markers):
        if marker.start() >= offset:
            return marker_index, marker
    return None


def extract_english(pdf: PdfText, marker_index: int) -> str:
    marker = pdf.markers[marker_index]
    end = pdf.markers[marker_index + 1].start() if marker_index + 1 < len(pdf.markers) else len(pdf.text)
    lines = pdf.text[marker.start() : end].splitlines()
    kept: list[str] = []
    for line in lines:
        line = clean_ws(line)
        if not line or PAGE_NOISE_RE.match(line):
            continue
        arabic_count = len(re.findall(r"[\u0600-\u06ff]", line))
        latin_count = len(re.findall(r"[A-Za-z]", line))
        if arabic_count > latin_count:
            continue
        kept.append(line)
    return clean_ws(" ".join(kept))


def extract_following_english(pdf: PdfText, arabic_offset: int) -> str:
    """Extract the English block immediately following an Arabic PDF block."""

    lines = pdf.text.splitlines(keepends=True)
    cursor = 0
    line_index = 0
    for index, line in enumerate(lines):
        if cursor + len(line) > arabic_offset:
            line_index = index
            break
        cursor += len(line)
    started = False
    kept: list[str] = []
    for line in lines[line_index:]:
        value = clean_ws(line)
        if not value or PAGE_NOISE_RE.match(value):
            continue
        if SOURCE_FOOTNOTE_RE.match(value):
            if started:
                break
            continue
        arabic_count = len(re.findall(r"[\u0600-\u06ff]", value))
        latin_count = len(re.findall(r"[A-Za-z]", value))
        if arabic_count > latin_count:
            if started:
                break
            continue
        if latin_count:
            started = True
            kept.append(value)
    return clean_ws(" ".join(kept))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_directory", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--public-id", action="append", default=[])
    args = parser.parse_args()
    pdfs = load_pdf_texts(args.pdf_directory)

    with SessionLocal() as db:
        book = db.execute(select(Book).where(Book.source_book_id == "11005")).scalar_one()
        hadiths = list(
            db.execute(
                select(Hadith)
                .where(
                    Hadith.book_id == book.id,
                    Hadith.review_status != "rejected_non_hadith_fragment",
                )
                .order_by(Hadith.sequence_in_book)
            ).scalars()
        )
        translations = list(
            db.execute(
                select(HadithTranslation).where(
                    HadithTranslation.language == "en",
                    HadithTranslation.translation_version == TRANSLATION_VERSION,
                )
            ).scalars()
        )
        hadith_by_id = {row.id: row for row in hadiths}
        current = {
            row.hadith_id
            for row in translations
            if row.hadith_id in hadith_by_id
            and row.status in PUBLIC_STATUSES
            and row.risk_level == "green"
            and clean_ws(row.matn_translation)
            and row.source_full_sha256 == sha256_text(hadith_by_id[row.hadith_id].full_text_raw)
        }
        missing = [row for row in hadiths if row.id not in current]
        if args.public_id:
            requested = set(args.public_id)
            missing = [row for row in missing if row.public_id in requested]
        max_page_by_volume: dict[int, int] = {}
        for hadith in hadiths:
            volume = hadith.volume_start or 0
            max_page_by_volume[volume] = max(
                max_page_by_volume.get(volume, 0), hadith.page_end
            )

    results: list[dict[str, object]] = []
    for hadith in missing:
        if hadith.volume_start == 8 and hadith.printed_number:
            try:
                expected_number = 14448 + int(hadith.printed_number)
            except ValueError:
                expected_number = None
            if expected_number is not None:
                found = next(
                    (
                        (pdf, index, marker)
                        for pdf in pdfs
                        if pdf.volume == 8
                        for index, marker in enumerate(pdf.markers)
                        if int(marker.group(1)) == expected_number
                    ),
                    None,
                )
                if found:
                    pdf, marker_index, marker = found
                    results.append(
                        {
                            "public_id": hadith.public_id,
                            "volume": 8,
                            "page_start": hadith.page_start,
                            "printed_number": hadith.printed_number,
                            "matched": True,
                            "match_method": "volume8_printed_number",
                            "matched_word_count": None,
                            "distance_to_h_marker": None,
                            "hubeali_number": expected_number,
                            "source_url": pdf.source_url,
                            "source_text_path": str(pdf.path),
                            "matched_phrase": None,
                            "english": extract_english(pdf, marker_index),
                        }
                    )
                    continue
        words = arabic_words(hadith.full_text_raw)
        compact_matn, _ = compact_arabic_with_offsets(hadith.matn_raw)
        section_words = arabic_words(hadith.section_title or "")
        volume_pdfs = [pdf for pdf in pdfs if pdf.volume == hadith.volume_start]
        expected_position = 1.0
        if volume_pdfs:
            max_position = max(pdf.position for pdf in volume_pdfs)
            max_page = max_page_by_volume.get(hadith.volume_start or 0, hadith.page_end)
            if max_page > 1:
                expected_position = 1 + (hadith.page_start - 1) * (max_position - 1) / (max_page - 1)
        candidates: list[tuple[float, float, int, int, int, PdfText, str, str]] = []
        for pdf in pdfs:
            if pdf.volume != hadith.volume_start:
                continue
            if abs(pdf.position - expected_position) > 3.0:
                continue
            compact_match = find_compact_phrase(pdf, hadith.matn_raw)
            phrase_match = compact_match or find_phrase(pdf, words)
            if not phrase_match:
                continue
            width, offset, phrase = phrase_match
            method = "pdf_arabic_compact_chars" if compact_match else "pdf_arabic_longest_block"
            compact_coverage = width / max(1, min(len(compact_matn), 5000)) if compact_match else 0.0
            section_width = longest_block_size(pdf, section_words)
            position_distance = abs(pdf.position - expected_position)
            signal = (100 * compact_coverage + width / 20) if compact_match else width
            combined_score = signal + 1.5 * min(section_width, 12) - 2.0 * position_distance
            candidates.append(
                (combined_score, compact_coverage, section_width, width, -offset, pdf, phrase, method)
            )
        if candidates:
            combined_score, compact_coverage, section_width, width, negative_offset, pdf, phrase, method = max(
                candidates,
                key=lambda row: (row[0], row[3], row[2]),
            )
            offset = -negative_offset
            english = extract_following_english(pdf, offset)
            minimum_width = 24 if method == "pdf_arabic_compact_chars" else 4
            matched = width >= minimum_width and combined_score >= 4 and len(english) >= 20
            results.append(
                {
                    "public_id": hadith.public_id,
                    "volume": hadith.volume_start,
                    "page_start": hadith.page_start,
                    "printed_number": hadith.printed_number,
                    "matched": matched,
                    "match_method": method,
                    "matched_section_word_count": section_width,
                    "expected_pdf_position": expected_position,
                    "matched_pdf_position": pdf.position,
                    "combined_match_score": combined_score,
                    "compact_coverage": compact_coverage,
                    "matched_word_count": width,
                    "distance_to_h_marker": None,
                    "hubeali_number": None,
                    "source_url": pdf.source_url,
                    "source_text_path": str(pdf.path),
                    "matched_phrase": phrase,
                    "english": english if matched else None,
                }
            )
        else:
            results.append(
                {
                    "public_id": hadith.public_id,
                    "volume": hadith.volume_start,
                    "page_start": hadith.page_start,
                    "printed_number": hadith.printed_number,
                    "matched": False,
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    matched = sum(bool(row["matched"]) for row in results)
    print(f"missing={len(results)} matched={matched} output={args.output}")


if __name__ == "__main__":
    main()
