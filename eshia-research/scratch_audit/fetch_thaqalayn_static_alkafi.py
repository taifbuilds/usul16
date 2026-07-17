"""Fetch and cache ThaqalaynData Al-Kafi detail rows for translation matching.

This is a reproducible helper for the 2026-07 Al-Kafi translation import. It
normalizes the public static detail JSON into the compact row format consumed by
``eshia_research.translation.thaqalayn_importer``.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import httpx

from eshia_research.translation.thaqalayn_importer import (
    _static_hadith_paths,
    static_row_from_detail,
)


NETLIFY_BASE = "https://thaqalayndata.netlify.app"
RAW_BASE = "https://raw.githubusercontent.com/narmafraz/ThaqalaynData/master"


def detail_urls(path: str) -> tuple[str, str]:
    suffix = f"{path.replace(':', '/')}.json"
    return f"{NETLIFY_BASE}{suffix}", f"{RAW_BASE}{suffix}"


def fetch_manifest(timeout: float) -> list[str]:
    response = httpx.get(
        f"{NETLIFY_BASE}/books/complete/al-kafi.json",
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "Usul16 translation importer"},
    )
    response.raise_for_status()
    return _static_hadith_paths(response.json())


def fetch_row(path: str, timeout: float) -> dict[str, Any]:
    last_error = ""
    for url in detail_urls(path):
        try:
            response = httpx.get(
                url,
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": "Usul16 translation importer"},
            )
            response.raise_for_status()
            return static_row_from_detail(response.json(), fallback_path=path)
        except Exception as exc:  # pragma: no cover - live network helper
            last_error = f"{type(exc).__name__}: {exc}"
    return {"path": path, "error": last_error}


def save_rows(output: Path, rows: list[dict[str, Any]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda row: (int(row.get("volume") or 0), int(row.get("index") or 0), str(row.get("path") or "")))
    temp = output.with_suffix(output.suffix + ".tmp")
    temp.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    temp.replace(output)


def load_existing(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--flush-every", type=int, default=100)
    args = parser.parse_args()

    output = Path(args.output)
    rows = load_existing(output)
    if args.seed:
        seed = load_existing(Path(args.seed))
        known = {str(row.get("path") or "") for row in rows}
        rows.extend(row for row in seed if str(row.get("path") or "") not in known)

    seen = {str(row.get("path") or "") for row in rows if row.get("path")}
    paths = fetch_manifest(args.timeout)
    pending = [path for path in paths if path not in seen]
    print(f"manifest_paths={len(paths)} existing={len(rows)} pending={len(pending)}", flush=True)

    started = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(fetch_row, path, args.timeout) for path in pending]
        for future in as_completed(futures):
            rows.append(future.result())
            completed += 1
            if completed % args.flush_every == 0:
                save_rows(output, rows)
                errors = sum(1 for row in rows if row.get("error"))
                elapsed = time.time() - started
                print(
                    f"completed={completed}/{len(pending)} total_rows={len(rows)} "
                    f"errors={errors} elapsed={elapsed:.1f}s",
                    flush=True,
                )

    save_rows(output, rows)
    errors = sum(1 for row in rows if row.get("error"))
    usable = sum(1 for row in rows if row.get("arabic_text") and (row.get("en_sarwar") or row.get("en_hubeali")))
    print(f"done total_rows={len(rows)} usable={usable} errors={errors}", flush=True)


if __name__ == "__main__":
    main()
