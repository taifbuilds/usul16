"""Map ThaqalaynData HubeAli rows back to the original HubeAli PDF numbers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from match_hubeali_pdf_translations import extract_english, load_pdf_texts


LATIN_TOKEN_RE = re.compile(r"[a-z0-9]+")
H_PREFIX_RE = re.compile(r"^h\s*\d+\s*[-–]\s*", re.IGNORECASE)


def tokens(text: str) -> list[str]:
    return LATIN_TOKEN_RE.findall(H_PREFIX_RE.sub("", text).lower())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_directory", type=Path)
    parser.add_argument("static_cache", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    pdf_records: list[dict[str, object]] = []
    prefix_index: dict[tuple[str, ...], list[int]] = {}
    for pdf in load_pdf_texts(args.pdf_directory):
        for marker_index, marker in enumerate(pdf.markers):
            english = extract_english(pdf, marker_index)
            english_tokens = tokens(english)
            if len(english_tokens) < 12:
                continue
            record_index = len(pdf_records)
            pdf_records.append(
                {
                    "volume": pdf.volume,
                    "hubeali_number": int(marker.group(1)),
                    "source_url": pdf.source_url,
                    "source_text_path": str(pdf.path),
                    "english": english,
                    "tokens": english_tokens,
                }
            )
            prefix_index.setdefault(tuple(english_tokens[:12]), []).append(record_index)

    static_rows = json.loads(args.static_cache.read_text(encoding="utf-8"))
    mappings: list[dict[str, object]] = []
    for row in static_rows:
        hubeali = str(row.get("en_hubeali") or "")
        static_tokens = tokens(hubeali)
        if len(static_tokens) < 12:
            continue
        candidate_indexes = prefix_index.get(tuple(static_tokens[:12]), [])
        candidates = [
            pdf_records[index]
            for index in candidate_indexes
            if int(pdf_records[index]["volume"]) == int(row.get("volume") or 0)
        ]
        if len(candidates) != 1:
            continue
        candidate = candidates[0]
        mappings.append(
            {
                "volume": int(row["volume"]),
                "remote_id": int(row["index"]),
                "path": row.get("path"),
                "hubeali_number": candidate["hubeali_number"],
                "source_url": candidate["source_url"],
                "source_text_path": candidate["source_text_path"],
                "english": candidate["english"],
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(mappings, ensure_ascii=False, indent=2), encoding="utf-8")
    counts: dict[int, int] = {}
    for row in mappings:
        volume = int(row["volume"])
        counts[volume] = counts.get(volume, 0) + 1
    print(
        f"pdf_records={len(pdf_records)} static_rows={len(static_rows)} "
        f"mapped={len(mappings)} by_volume={counts} output={args.output}"
    )


if __name__ == "__main__":
    main()
