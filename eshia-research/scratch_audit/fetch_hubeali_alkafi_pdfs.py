"""Download and text-extract the HubeAli Al-Kafi source PDFs for audit."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urljoin

import httpx
from pypdf import PdfReader


PDF_LINK_RE = re.compile(r'href=["\']([^"\']+\.pdf)["\']', re.IGNORECASE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--volumes", default="1,5,6,7,8")
    args = parser.parse_args()
    volumes = [int(value) for value in args.volumes.split(",")]
    args.output.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []

    with httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "Usul16 source verification audit"},
    ) as client:
        for volume in volumes:
            slug = "alkafivol5e" if volume == 5 else f"alkafivol{volume}"
            page_url = f"https://www.hubeali.com/{slug}/"
            response = client.get(page_url)
            response.raise_for_status()
            urls = []
            for href in PDF_LINK_RE.findall(response.text):
                url = urljoin(page_url, html.unescape(href)).replace("http://", "https://")
                folder = f"/alkafi-volume{volume}/" if volume == 8 else f"/alkafivol{volume}/"
                if folder not in unquote(url).lower():
                    continue
                if url not in urls:
                    urls.append(url)
            for position, url in enumerate(urls, start=1):
                stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", unquote(url.rsplit("/", 1)[-1]))
                pdf_path = args.output / f"v{volume:02d}-{position:02d}-{stem}"
                if not pdf_path.exists():
                    pdf_response = client.get(url)
                    pdf_response.raise_for_status()
                    pdf_path.write_bytes(pdf_response.content)
                text_path = pdf_path.with_suffix(pdf_path.suffix + ".txt")
                extraction_error = None
                if not text_path.exists():
                    try:
                        reader = PdfReader(str(pdf_path))
                        text = "\n\f\n".join(page.extract_text() or "" for page in reader.pages)
                        text_path.write_text(text, encoding="utf-8")
                    except Exception as exc:  # pragma: no cover - live-source variance
                        extraction_error = str(exc)
                manifest.append(
                    {
                        "volume": volume,
                        "position": position,
                        "source_page": page_url,
                        "source_url": url,
                        "pdf_path": str(pdf_path),
                        "text_path": str(text_path),
                        "bytes": pdf_path.stat().st_size,
                        "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
                        "extraction_error": extraction_error,
                    }
                )
                print(f"v{volume} {position}/{len(urls)} {pdf_path.name}")

    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"files={len(manifest)} manifest={args.output / 'manifest.json'}")


if __name__ == "__main__":
    main()
