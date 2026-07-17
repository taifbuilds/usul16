"""Extract numbered Muhammad Sarwar records from the eight Al-Kafi PDFs.

The output is an audit cache, not a publication artifact.  Each record keeps
its PDF/page identity and checksum so later Arabic alignment remains
reproducible without placing the source PDFs in the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader


MARKER_RE = re.compile(
    r"(?m)^H\s*(\d{1,6})(?:\s*\([a-z]\))?\s*,\s*Ch\.\s*([^,\n]+),\s*h\s*([^\n]+)"
)
SPACE_RE = re.compile(r"[ \t\r\f\v]+")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_text(value: str) -> str:
    lines = [SPACE_RE.sub(" ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    records: list[dict[str, object]] = []
    manifest: list[dict[str, object]] = []
    for volume in range(1, 9):
        path = args.pdf_directory / f"Al-Kafi_Volume-{volume}.pdf"
        reader = PdfReader(path)
        page_texts: list[str] = []
        page_starts: list[int] = []
        cursor = 0
        for page in reader.pages:
            page_starts.append(cursor)
            text = page.extract_text() or ""
            page_texts.append(text)
            cursor += len(text) + 1
        full_text = "\n".join(page_texts)
        markers = list(MARKER_RE.finditer(full_text))
        checksum = sha256_file(path)
        manifest.append(
            {
                "volume": volume,
                "path": str(path),
                "pages": len(reader.pages),
                "sha256": checksum,
                "record_count": len(markers),
                "source_url": (
                    "https://al-murtaza.org/wp-content/uploads/2021/08/"
                    f"Al-Kafi_Volume-{volume}.pdf"
                ),
            }
        )
        page_index = 0
        for index, marker in enumerate(markers):
            while (
                page_index + 1 < len(page_starts)
                and page_starts[page_index + 1] <= marker.start()
            ):
                page_index += 1
            end = markers[index + 1].start() if index + 1 < len(markers) else len(full_text)
            records.append(
                {
                    "volume": volume,
                    "hadith_number": int(marker.group(1)),
                    "chapter_number": marker.group(2).strip(),
                    "number_in_chapter": marker.group(3).strip(),
                    "pdf_page": page_index + 1,
                    "source_url": manifest[-1]["source_url"],
                    "source_sha256": checksum,
                    "english": clean_text(full_text[marker.start() : end]),
                }
            )
        print(
            f"volume={volume} pages={len(reader.pages)} records={len(markers)}",
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
