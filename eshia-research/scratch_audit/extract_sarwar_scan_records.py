"""Extract numbered Muhammad Sarwar records from selected published scans.

This is an audit/source-recovery tool.  Each output record retains the PDF
checksum, physical page, marker, and source URL.  HubeAli-labelled pages in a
hybrid scan are explicitly excluded even if the surrounding PDF is branded as
a Sarwar volume.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf


MARKER_RE = re.compile(
    r"(?mi)^\s*H\s*(\d{1,6})([a-z]?)\s*,\s*C(?:h|H)\.?\s*([^,\n]+),\s*h\s*([^\n]+)"
)
SPACE_RE = re.compile(r"\s+")
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
DROP_LINE_RE = re.compile(
    r"^(?:https?://|www\.hubeali\.com|Al-?Kafi\s*[–-]\s*Vol\.|Alkafi Volume|\d+\s+out of\s+\d+)",
    re.IGNORECASE,
)
RECORD_STOP_RE = re.compile(
    r"(?mi)^\s*(?:Chapter\s+\d+\s*[-–]|Part\s+(?:One|Two|Three|Four|Five)\s*:|"
    r"End of the Book|Table of Contents|Alkafi Volume|www\.hubeali\.com)"
)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_record(value: str) -> str:
    stop = RECORD_STOP_RE.search(value)
    if stop:
        value = value[: stop.start()]
    kept: list[str] = []
    for raw_line in value.splitlines():
        line = SPACE_RE.sub(" ", raw_line).strip()
        if not line or DROP_LINE_RE.match(line):
            continue
        arabic = len(ARABIC_RE.findall(line))
        if arabic and arabic / max(len(line), 1) > 0.20:
            continue
        kept.append(line)
    return SPACE_RE.sub(" ", " ".join(kept)).strip()


def parse_pdf_argument(value: str) -> tuple[int, Path, str]:
    try:
        volume_text, path_text, source_url = value.split("=", 2)
        return int(volume_text), Path(path_text), source_url
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "--pdf must be VOLUME=PATH=SOURCE_URL"
        ) from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--pdf",
        action="append",
        required=True,
        type=parse_pdf_argument,
        help="VOLUME=PATH=SOURCE_URL; repeat for each scan",
    )
    args = parser.parse_args()

    records: list[dict[str, object]] = []
    manifest: list[dict[str, object]] = []
    for volume, path, source_url in args.pdf:
        document = pymupdf.open(path)
        page_texts = [page.get_text("text") for page in document]
        page_starts: list[int] = []
        cursor = 0
        for text in page_texts:
            page_starts.append(cursor)
            cursor += len(text) + 1
        full_text = "\n".join(page_texts)
        markers = list(MARKER_RE.finditer(full_text))
        digest = checksum(path)
        manifest.append(
            {
                "volume": volume,
                "path": str(path),
                "source_url": source_url,
                "pages": len(document),
                "sha256": digest,
                "markers": len(markers),
            }
        )
        page_index = 0
        accepted = 0
        for index, marker in enumerate(markers):
            while (
                page_index + 1 < len(page_starts)
                and page_starts[page_index + 1] <= marker.start()
            ):
                page_index += 1
            end = markers[index + 1].start() if index + 1 < len(markers) else len(full_text)
            raw = full_text[marker.end() : end]
            # The public Volume 7 scan inserts explicitly branded HubeAli books
            # between Sarwar's H 13292 and H 14104.  No H-marked record is taken
            # from those pages, and the guard prevents accidental future reuse.
            page_text = page_texts[page_index]
            if "www.hubeali.com" in page_text.lower():
                continue
            english = clean_record(raw)
            if not english:
                continue
            records.append(
                {
                    "physical_volume": volume,
                    "hadith_number": int(marker.group(1)),
                    "hadith_suffix": marker.group(2) or None,
                    "chapter_number": marker.group(3).strip(),
                    "number_in_chapter": marker.group(4).strip(),
                    "pdf_page": page_index + 1,
                    "marker": SPACE_RE.sub(" ", marker.group(0)).strip(),
                    "source_url": source_url,
                    "source_sha256": digest,
                    "english": english,
                }
            )
            accepted += 1
        print(
            f"volume={volume} pages={len(document)} markers={len(markers)} accepted={accepted}",
            flush=True,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"manifest": manifest, "records": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"records={len(records)} output={args.output}")


if __name__ == "__main__":
    main()
