"""Website-first completeness audits for the Four Books on Thaqalayn.

The live website is the witness. API-derived structure rows and translation
provenance are used only as candidate links, then reverified against Arabic
rendered on ``thaqalayn.net`` chapter pages. The audit is read-only.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import threading
import time
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field, replace
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from eshia_research.hadith_extractor import split_isnad_matn
from eshia_research.models import (
    Book,
    Hadith,
    HadithSplitReview,
    HadithTranslation,
    ThaqalaynStructureMap,
)
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.thaqalayn_importer import match_norm
from eshia_research.translation.publication import is_public_english_translation
from eshia_research.translation.text import clean_ws, sha256_text


BASE_URL = "https://thaqalayn.net"
ROBOTS_URL = f"{BASE_URL}/robots.txt"
HADITH_SITEMAP_URL = f"{BASE_URL}/sitemap/hadith-0.xml"
USER_AGENT = "Usul16 completeness audit (contact: local research project)"
WEBSITE_TRANSLATION_VERSION = "thaqalayn_website_v1"
WEBSITE_PROVIDER = "thaqalayn-website"
WEBSITE_QA_VERSION = "thaqalayn_website_arabic_match_v1"

_CHAPTER_PATH_RE = re.compile(r"^/chapter/(\d+)/(\d+)/(\d+)$")
_HADITH_PATH_RE = re.compile(r"^/hadith/(\d+)/(\d+)/(\d+)/(\d+)$")
_LEGACY_PATH_RE = re.compile(r"^/books/al-kafi:(\d+):(\d+):(\d+):(\d+)$")
_ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06ff]")


@dataclass(frozen=True)
class WebsiteCorpus:
    key: str
    title: str
    source_book_id: str
    website_volumes: tuple[tuple[int, int], ...]
    translator: str
    schema_version: str

    @property
    def website_book_ids(self) -> frozenset[int]:
        return frozenset(remote_id for _, remote_id in self.website_volumes)


AL_KAFI_CORPUS = WebsiteCorpus(
    key="alkafi",
    title="Al-Kafi",
    source_book_id="11005",
    website_volumes=tuple((volume, volume) for volume in range(1, 9)),
    translator="Muhammad Sarwar",
    schema_version="alkafi-thaqalayn-website-v1",
)
FAQIH_CORPUS = WebsiteCorpus(
    key="faqih",
    title="Man La Yahduruhu al-Faqih",
    source_book_id="11021",
    website_volumes=((1, 34), (2, 35), (3, 36), (4, 37)),
    translator="Bab Ul Qaim Publications",
    schema_version="faqih-thaqalayn-website-v1",
)
WEBSITE_CORPORA = {
    corpus.key: corpus for corpus in (AL_KAFI_CORPUS, FAQIH_CORPUS)
}


def get_website_corpus(key: str) -> WebsiteCorpus:
    try:
        return WEBSITE_CORPORA[key.casefold()]
    except KeyError as exc:
        choices = ", ".join(sorted(WEBSITE_CORPORA))
        raise ValueError(f"Unknown website corpus {key!r}; choose one of: {choices}") from exc


def _corpus_from_inventory(inventory: dict[str, Any]) -> WebsiteCorpus:
    key = str(inventory.get("corpus_key") or "alkafi")
    corpus = get_website_corpus(key)
    source_book_id = str(inventory.get("source_book_id") or corpus.source_book_id)
    if source_book_id != corpus.source_book_id:
        raise ValueError("Website inventory source book does not match its corpus")
    return corpus


def _sha256(value: str | bytes) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest()


def _digits_only(value: str | None) -> int | None:
    text = clean_ws(value)
    if not text:
        return None
    digits: list[str] = []
    for char in text:
        try:
            digits.append(str(unicodedata.digit(char)))
        except (TypeError, ValueError):
            return None
    return int("".join(digits)) if digits else None


def _website_global_number(row: dict[str, Any]) -> int | None:
    for value in (row.get("arabic_text"), row.get("english_text")):
        match = re.match(
            r"\s*(?:Hadith[.]\s*)?([0-9٠-٩۰-۹]+)\s*[-–—.]",
            str(value or ""),
            re.IGNORECASE,
        )
        if match:
            return _digits_only(match.group(1))
    return None


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    temp.replace(path)


def canonical_hadith_path(value: str | None) -> str | None:
    if not value:
        return None
    path = urlparse(value).path.rstrip("/")
    if _HADITH_PATH_RE.fullmatch(path):
        return path
    legacy = _LEGACY_PATH_RE.fullmatch(path)
    if legacy:
        return "/hadith/" + "/".join(legacy.groups())
    return None


@dataclass(frozen=True)
class WebsiteHadith:
    path: str
    chapter_path: str
    volume: int
    remote_book_id: int
    kitab_id: int
    kitab_name_en: str
    chapter_id: int
    chapter_name_en: str
    number_in_chapter: int
    arabic_text: str
    english_text: str
    arabic_sha256: str

    @property
    def url(self) -> str:
        return f"{BASE_URL}{self.path}"


@dataclass
class WebsiteEnglishImportStats:
    considered: int = 0
    imported: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped_non_one_to_one: int = 0
    skipped_missing_english: int = 0
    skipped_stale_arabic_match: int = 0
    skipped_unknown_translator: int = 0
    boundary_exact: int = 0
    boundary_marker: int = 0
    boundary_full_fallback: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class WebsiteStructureImportStats:
    confirmed: int = 0
    matched: int = 0
    interpolated: int = 0
    unmapped: int = 0
    written: int = 0


@dataclass
class WebsiteGapImportStats:
    considered: int = 0
    created_hadiths: int = 0
    created_translations: int = 0
    skipped_existing: int = 0


@dataclass
class WebsiteBoundaryRepairStats:
    considered: int = 0
    boundaries_repaired: int = 0
    split_records_created: int = 0
    unchanged: int = 0
    skipped_complex_relations: int = 0


def _key_list_sha256(values: list[str] | set[str]) -> str:
    return _sha256(json.dumps(sorted(values), ensure_ascii=False, separators=(",", ":")))


def _local_only_evidence_sha256(rows: list[Hadith]) -> str:
    evidence = [
        {
            "public_id": row.public_id,
            "arabic_sha256": sha256_text(clean_ws(row.full_text_raw)),
            "printed_number": row.printed_number,
            "volume": row.volume_start,
            "page_start": row.page_start,
        }
        for row in rows
    ]
    return _sha256(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def parse_book_chapter_paths(
    html: str,
    *,
    volume: int,
    remote_book_id: int | None = None,
) -> list[str]:
    expected_book_id = remote_book_id if remote_book_id is not None else volume
    soup = BeautifulSoup(html, "lxml")
    paths = {
        (urlparse(link.get("href") or "").path.rstrip("/"))
        for link in soup.find_all("a", href=True)
    }
    return sorted(
        (
            path
            for path in paths
            if (match := _CHAPTER_PATH_RE.fullmatch(path))
            and int(match.group(1)) == expected_book_id
        ),
        key=lambda path: tuple(int(part) for part in path.rsplit("/", 3)[1:]),
    )


def parse_book_chapter_structure(
    html: str,
    *,
    remote_book_id: int,
) -> dict[str, tuple[str, str]]:
    """Read kitab and chapter labels from a rendered Thaqalayn book page."""

    soup = BeautifulSoup(html, "lxml")
    current_kitab = ""
    result: dict[str, tuple[str, str]] = {}
    for node in soup.find_all(["h2", "a"]):
        if node.name == "h2":
            heading = clean_ws(node.get_text(" ", strip=True))
            current_kitab = re.sub(r"^\d+[.]\s*", "", heading).strip()
            continue
        path = urlparse(node.get("href") or "").path.rstrip("/")
        match = _CHAPTER_PATH_RE.fullmatch(path)
        if match is None or int(match.group(1)) != remote_book_id:
            continue
        label = clean_ws(node.get_text(" ", strip=True))
        chapter_name = re.sub(r"^Chapter\s+\d+\s*[-–—]\s*", "", label)
        chapter_name = re.sub(
            r"\s+\d+\s+(?:Aḥadīth|Ḥadīth)\s*$", "", chapter_name
        ).strip()
        result[path] = (current_kitab or "Content", chapter_name or label)
    return result


def parse_sitemap_paths(xml: str, *, website_book_ids: set[int] | frozenset[int]) -> list[str]:
    root = ElementTree.fromstring(xml)
    paths = {
        urlparse(node.text.strip()).path.rstrip("/")
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] == "loc" and node.text
    }
    return sorted(
        (
            path
            for path in paths
            if (match := _HADITH_PATH_RE.fullmatch(path))
            and int(match.group(1)) in website_book_ids
        ),
        key=lambda path: tuple(int(part) for part in path.rsplit("/", 4)[1:]),
    )


def parse_alkafi_sitemap_paths(xml: str) -> list[str]:
    """Backward-compatible Al-Kafi sitemap parser used by older callers."""

    return parse_sitemap_paths(xml, website_book_ids=AL_KAFI_CORPUS.website_book_ids)


def parse_chapter_page(
    html: str,
    *,
    chapter_path: str,
    volume: int | None = None,
    kitab_name_en: str = "",
    chapter_name_en: str = "",
    non_report_entries: list[dict[str, str]] | None = None,
    anomalies: list[dict[str, str]] | None = None,
) -> list[WebsiteHadith]:
    chapter_match = _CHAPTER_PATH_RE.fullmatch(chapter_path)
    if not chapter_match:
        raise ValueError(f"Invalid Thaqalayn chapter path: {chapter_path}")
    expected_remote_book, expected_kitab, expected_chapter = map(
        int, chapter_match.groups()
    )
    local_volume = volume if volume is not None else expected_remote_book
    soup = BeautifulSoup(html, "lxml")
    if not chapter_name_en:
        title = soup.find("meta", attrs={"property": "og:title"})
        page_title = clean_ws(title.get("content")) if title else ""
        chapter_name_en = page_title.rsplit(":", 1)[-1].strip()
    rows: list[WebsiteHadith] = []
    for article in soup.find_all("article"):
        link = article.find("a", href=_HADITH_PATH_RE)
        if link is not None:
            path = urlparse(link.get("href") or "").path.rstrip("/")
        else:
            heading = article.find(["h2", "h3", "h4"])
            heading_text = heading.get_text(" ", strip=True) if heading else ""
            heading_match = re.search(
                r"(?:Hadith|Ḥadīth)\s+(\d+)\b",
                heading_text,
                re.IGNORECASE,
            )
            if heading_match is None:
                continue
            number = int(heading_match.group(1))
            path = (
                f"/hadith/{expected_remote_book}/{expected_kitab}/"
                f"{expected_chapter}/{number}"
            )
        match = _HADITH_PATH_RE.fullmatch(path)
        if match is None:
            continue
        remote_book_id, kitab_id, chapter_id, number = map(int, match.groups())
        if (remote_book_id, kitab_id, chapter_id) != (
            expected_remote_book,
            expected_kitab,
            expected_chapter,
        ):
            raise ValueError(f"Hadith path {path} does not belong to {chapter_path}")
        arabic = article.find(attrs={"dir": "rtl", "lang": "ar"})
        english_text = ""
        if arabic is None:
            label = " ".join(article.get_text(" ", strip=True).split())
            if "Part of Previous Chapter" in label:
                if non_report_entries is not None:
                    non_report_entries.append(
                        {
                            "path": path,
                            "classification": "non_report_placeholder",
                            "label": label,
                        }
                    )
                continue
            paragraphs = [
                " ".join(node.get_text(" ", strip=True).split())
                for node in article.find_all("p")
                if node.get_text(" ", strip=True)
            ]
            combined = " ".join(paragraphs)
            marker = re.search(rf"\s{number}[.]\s", combined)
            if _ARABIC_CHAR_RE.search(combined) and marker is not None:
                arabic_text = combined[: marker.start()].strip()
                english_text = combined[marker.start() + 1 :].strip()
                classification = "combined_arabic_english_paragraph"
            else:
                arabic_text = ""
                english_text = combined
                classification = "website_missing_arabic"
            if anomalies is not None:
                anomalies.append(
                    {
                        "path": path,
                        "classification": classification,
                    }
                )
        else:
            arabic_text = " ".join(arabic.get_text(" ", strip=True).split())
            english_candidates = [
                node
                for node in article.find_all("p")
                if node is not arabic and node.get_text(" ", strip=True)
            ]
            english_text = (
                " ".join(english_candidates[0].get_text(" ", strip=True).split())
                if english_candidates
                else ""
            )
        rows.append(
            WebsiteHadith(
                path=path,
                chapter_path=chapter_path,
                volume=local_volume,
                remote_book_id=remote_book_id,
                kitab_id=kitab_id,
                kitab_name_en=kitab_name_en or f"Book {kitab_id}",
                chapter_id=chapter_id,
                chapter_name_en=chapter_name_en or f"Chapter {chapter_id}",
                number_in_chapter=number,
                arabic_text=arabic_text,
                english_text=english_text,
                arabic_sha256=_sha256(arabic_text),
            )
        )
    merged: dict[str, WebsiteHadith] = {}
    for row in rows:
        existing = merged.get(row.path)
        if existing is None:
            merged[row.path] = row
            continue
        arabic_text = max((existing.arabic_text, row.arabic_text), key=len)
        english_text = max((existing.english_text, row.english_text), key=len)
        merged[row.path] = replace(
            existing,
            arabic_text=arabic_text,
            english_text=english_text,
            arabic_sha256=_sha256(arabic_text),
        )
        if anomalies is not None:
            anomalies.append(
                {
                    "path": row.path,
                    "classification": "duplicate_website_articles_merged",
                }
            )
    return sorted(merged.values(), key=lambda row: row.number_in_chapter)


class _RateLimiter:
    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = max(0.0, delay_seconds)
        self._lock = threading.Lock()
        self._last_request = 0.0

    def wait(self) -> None:
        with self._lock:
            remaining = self.delay_seconds - (time.monotonic() - self._last_request)
            if remaining > 0:
                time.sleep(remaining)
            self._last_request = time.monotonic()


def _fetch_text(
    client: httpx.Client,
    limiter: _RateLimiter,
    url: str,
    *,
    retries: int = 3,
) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        limiter.wait()
        try:
            response = client.get(url)
            response.raise_for_status()
            return response.text
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def _chapter_cache_path(cache_dir: Path, chapter_path: str) -> Path:
    match = _CHAPTER_PATH_RE.fullmatch(chapter_path)
    if match is None:
        raise ValueError(chapter_path)
    return cache_dir.joinpath("chapters", *match.groups()).with_suffix(".json")


def crawl_thaqalayn_website(
    *,
    corpus: WebsiteCorpus,
    inventory_path: Path,
    cache_dir: Path,
    workers: int = 4,
    delay_seconds: float = 0.2,
    timeout_seconds: float = 30.0,
    refresh: bool = False,
    on_progress: Any | None = None,
) -> dict[str, Any]:
    """Inventory one rendered Thaqalayn corpus with a resumable compact cache."""

    limiter = _RateLimiter(delay_seconds)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    client = httpx.Client(
        timeout=timeout_seconds,
        follow_redirects=True,
        headers=headers,
        limits=httpx.Limits(max_connections=max(2, workers), max_keepalive_connections=max(2, workers)),
    )
    try:
        robots = _fetch_text(client, limiter, ROBOTS_URL)
        if re.search(r"(?im)^Disallow:\s*/\s*$", robots):
            raise RuntimeError("Thaqalayn robots.txt disallows crawling")
        sitemap_xml = _fetch_text(client, limiter, HADITH_SITEMAP_URL)
        sitemap_paths = parse_sitemap_paths(
            sitemap_xml, website_book_ids=corpus.website_book_ids
        )
        if not sitemap_paths:
            raise RuntimeError(
                f"No {corpus.title} paths found in the Thaqalayn hadith sitemap"
            )

        chapter_paths: set[str] = set()
        chapter_labels: dict[str, tuple[str, str]] = {}
        book_evidence: list[dict[str, Any]] = []
        volume_by_remote_book: dict[int, int] = {}
        for volume, remote_book_id in corpus.website_volumes:
            volume_by_remote_book[remote_book_id] = volume
            url = f"{BASE_URL}/book/{remote_book_id}"
            html = _fetch_text(client, limiter, url)
            paths = parse_book_chapter_paths(
                html, volume=volume, remote_book_id=remote_book_id
            )
            if not paths:
                raise RuntimeError(f"No chapters found on {url}")
            chapter_paths.update(paths)
            chapter_labels.update(
                parse_book_chapter_structure(html, remote_book_id=remote_book_id)
            )
            book_evidence.append(
                {
                    "volume": volume,
                    "remote_book_id": remote_book_id,
                    "url": url,
                    "page_sha256": _sha256(html),
                    "chapter_count": len(paths),
                }
            )

        ordered_paths = sorted(
            chapter_paths,
            key=lambda path: tuple(int(part) for part in path.rsplit("/", 3)[1:]),
        )
        chapter_results: dict[str, dict[str, Any]] = {}
        pending: list[str] = []
        for chapter_path in ordered_paths:
            cache_path = _chapter_cache_path(cache_dir, chapter_path)
            if cache_path.exists() and not refresh:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                if cached.get("schema_version") == corpus.schema_version:
                    chapter_results[chapter_path] = cached
                    continue
            pending.append(chapter_path)

        def fetch_chapter(chapter_path: str) -> tuple[str, dict[str, Any]]:
            url = f"{BASE_URL}{chapter_path}"
            html = _fetch_text(client, limiter, url)
            match = _CHAPTER_PATH_RE.fullmatch(chapter_path)
            if match is None:
                raise ValueError(chapter_path)
            remote_book_id = int(match.group(1))
            kitab_name_en, chapter_name_en = chapter_labels.get(
                chapter_path, (f"Book {match.group(2)}", f"Chapter {match.group(3)}")
            )
            non_report_entries: list[dict[str, str]] = []
            anomalies: list[dict[str, str]] = []
            rows = parse_chapter_page(
                html,
                chapter_path=chapter_path,
                volume=volume_by_remote_book[remote_book_id],
                kitab_name_en=kitab_name_en,
                chapter_name_en=chapter_name_en,
                non_report_entries=non_report_entries,
                anomalies=anomalies,
            )
            value = {
                "schema_version": corpus.schema_version,
                "chapter_path": chapter_path,
                "url": url,
                "page_sha256": _sha256(html),
                "hadith_count": len(rows),
                "non_report_entries": non_report_entries,
                "anomalies": anomalies,
                "rows": [asdict(row) for row in rows],
            }
            _atomic_json(_chapter_cache_path(cache_dir, chapter_path), value)
            return chapter_path, value

        completed = len(chapter_results)
        if on_progress:
            on_progress(completed, len(ordered_paths))
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            futures = [executor.submit(fetch_chapter, path) for path in pending]
            for future in as_completed(futures):
                path, value = future.result()
                chapter_results[path] = value
                completed += 1
                if on_progress:
                    on_progress(completed, len(ordered_paths))

        rows = [
            row
            for chapter_path in ordered_paths
            for row in chapter_results[chapter_path]["rows"]
        ]
        path_counts = Counter(str(row["path"]) for row in rows)
        duplicates = sorted(path for path, count in path_counts.items() if count > 1)
        if duplicates:
            raise RuntimeError(f"Duplicate website hadith paths: {duplicates[:10]}")

        non_report_entries = [
            entry
            for path in ordered_paths
            for entry in chapter_results[path].get("non_report_entries", [])
        ]
        anomalies = [
            entry
            for path in ordered_paths
            for entry in chapter_results[path].get("anomalies", [])
        ]
        rendered_paths = set(path_counts) | {
            str(entry["path"]) for entry in non_report_entries
        }
        sitemap_path_set = set(sitemap_paths)
        if rendered_paths != sitemap_path_set:
            missing = sorted(sitemap_path_set - rendered_paths)
            unexpected = sorted(rendered_paths - sitemap_path_set)
            raise RuntimeError(
                f"Rendered {corpus.title} paths do not match the hadith sitemap: "
                f"missing={missing[:10]}, unexpected={unexpected[:10]}"
            )

        inventory = {
            "schema_version": corpus.schema_version,
            "corpus_key": corpus.key,
            "title": corpus.title,
            "source_book_id": corpus.source_book_id,
            "translator": corpus.translator,
            "source": BASE_URL,
            "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "robots_sha256": _sha256(robots),
            "hadith_sitemap": {
                "url": HADITH_SITEMAP_URL,
                "page_sha256": _sha256(sitemap_xml),
                "path_count": len(sitemap_paths),
            },
            "books": book_evidence,
            "chapter_count": len(ordered_paths),
            "hadith_count": len(rows),
            "non_report_entries": non_report_entries,
            "anomalies": anomalies,
            "by_volume": dict(sorted(Counter(int(row["volume"]) for row in rows).items())),
            "chapters": [chapter_results[path] for path in ordered_paths],
        }
        _atomic_json(inventory_path, inventory)
        return inventory
    finally:
        client.close()


def crawl_alkafi_website(**kwargs: Any) -> dict[str, Any]:
    """Backward-compatible wrapper for the original Al-Kafi command."""

    return crawl_thaqalayn_website(corpus=AL_KAFI_CORPUS, **kwargs)


@lru_cache(maxsize=65_536)
def _cached_match_norm(value: str) -> str:
    return match_norm(value)


@lru_cache(maxsize=65_536)
def _cached_edition_norm(value: str) -> str:
    text = normalise_arabic_persian(clean_ws(value))
    text = text.replace("۝", " ")
    text = re.sub(
        r"(?:عل[يی]ه(?:ما|م|ن)?\s+السلام|صل[يی]\s+الله\s+عل[يی]ه(?:\s+و\s+آله)?)",
        " ",
        text,
    )
    text = re.sub(
        r"(?<![\u0600-\u06ff])[عص](?![\u0600-\u06ff])[\u200c\s]*[-–—:]?",
        " ",
        text,
    )
    return match_norm(text).replace("واله", "")


def _text_score(hadith: Hadith, website_text: str) -> float:
    remote_edition = _cached_edition_norm(website_text)
    local_editions = (
        _cached_edition_norm(hadith.matn_raw),
        _cached_edition_norm(hadith.full_text_raw),
    )
    if remote_edition and len(remote_edition) >= 12:
        if any(remote_edition in local for local in local_editions):
            return 1.0
    remote_norm = _cached_match_norm(website_text)
    local_full = _cached_match_norm(hadith.full_text_raw)
    local_matn = _cached_match_norm(hadith.matn_raw)
    if not remote_norm:
        return 0.0
    for left, right in ((local_matn, remote_norm), (remote_norm, local_full)):
        if left and (left == right or (len(left) >= 12 and left in right)):
            return 1.0
    # The editions often insert a short explanation or vary word forms while
    # preserving the report's order. Unordered word-set coverage both misses
    # those rows and overvalues repeated formulae. Ordered character blocks
    # retain direction and permit transparent one-sided additions.
    best = 0.0
    for local in local_editions:
        if min(len(local), len(remote_edition)) < 12:
            continue
        matcher = SequenceMatcher(None, local, remote_edition, autojunk=False)
        matched = sum(
            block.size for block in matcher.get_matching_blocks() if block.size >= 3
        )
        directional_coverage = matched / min(len(local), len(remote_edition))
        best = max(best, matcher.ratio(), directional_coverage)
    return best


def _inventory_rows(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for chapter in inventory.get("chapters", []) for row in chapter.get("rows", [])]


def _ordered_coverage(source_text: str, witness_texts: list[str]) -> float:
    """Return how much of the displayed Arabic is supported by website Arabic."""

    source = _cached_edition_norm(source_text)
    witness = "".join(_cached_edition_norm(text) for text in witness_texts)
    if not source or not witness:
        return 0.0
    matcher = SequenceMatcher(None, source, witness, autojunk=False)
    intervals = sorted(
        (block.a, block.a + block.size)
        for block in matcher.get_matching_blocks()
        if block.size >= 3
    )
    covered = 0
    end = 0
    for start, stop in intervals:
        if stop <= end:
            continue
        covered += stop - max(start, end)
        end = stop
    return min(1.0, covered / len(source))


def _publication_quality(
    db: Session,
    *,
    local_rows: list[Hadith],
    remote_by_path: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    unaccounted_local: list[Hadith],
    reviewed_local_only_ids: set[int] | None = None,
    minimum_coverage: float = 0.9,
) -> dict[str, Any]:
    """Audit the public record boundary, independently of inventory coverage."""

    local_by_id = {row.id: row for row in local_rows}
    local_ids = list(local_by_id)
    approved_reviews = {
        row.hadith_id: row
        for row in db.execute(
            select(HadithSplitReview).where(
                HadithSplitReview.hadith_id.in_(local_ids),
                HadithSplitReview.review_status == "approved",
                HadithSplitReview.approved_matn_raw.is_not(None),
            )
        ).scalars()
    }
    approved_boundaries = {
        hadith_id: clean_ws(
            " ".join(
                part
                for part in (row.approved_isnad_raw, row.approved_matn_raw)
                if part
            )
        )
        for hadith_id, row in approved_reviews.items()
    }
    website_translation_rows = list(
        db.execute(
            select(HadithTranslation).where(
                HadithTranslation.hadith_id.in_(local_ids),
                HadithTranslation.translation_version == WEBSITE_TRANSLATION_VERSION,
                HadithTranslation.status == "published",
                HadithTranslation.matn_translation.is_not(None),
            )
        ).scalars()
    )
    website_translations = {
        row.hadith_id
        for row in website_translation_rows
        if is_public_english_translation(row, local_by_id[row.hadith_id])
    }
    edges_by_local: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        edges_by_local[int(edge["local_id"])].append(edge)

    issues: list[dict[str, Any]] = []
    coverage_below_90 = 0
    coverage_below_75 = 0
    coverage_below_50 = 0
    non_one_to_one = 0
    missing_website_english = 0
    missing_published_translation = 0
    active_isnad_missing = 0
    accepted_boundary_relations = {
        "one_to_one",
        "website_continuation",
        "partial_website_continuation",
        "duplicate_website_occurrence",
        "website_field_anomaly",
    }
    partial_witness_relations = {
        "partial_website_continuation",
        "website_field_anomaly",
    }

    for local_id, local_edges in edges_by_local.items():
        hadith = local_by_id[local_id]
        paths = [str(edge["website_path"]) for edge in local_edges]
        remotes = [remote_by_path[path] for path in paths]
        displayed_arabic = approved_boundaries.get(local_id) or hadith.full_text_raw
        coverage = _ordered_coverage(
            displayed_arabic,
            [str(remote.get("arabic_text") or "") for remote in remotes],
        )
        relations = sorted({str(edge.get("relation") or "") for edge in local_edges})
        flags: list[str] = []
        coverage_is_required = not set(relations) <= partial_witness_relations
        if coverage < minimum_coverage and coverage_is_required:
            flags.append("website_arabic_covers_less_than_90_percent")
            coverage_below_90 += 1
        if coverage < 0.75 and coverage_is_required:
            coverage_below_75 += 1
        if coverage < 0.5 and coverage_is_required:
            coverage_below_50 += 1
        if not set(relations) <= accepted_boundary_relations:
            flags.append("non_one_to_one_record_boundary")
            non_one_to_one += 1
        review = approved_reviews.get(local_id)
        source_isnad, _ = split_isnad_matn(hadith.full_text_raw)
        if (
            review is not None
            and source_isnad
            and not review.approved_isnad_raw
            and review.split_version != "faqih_pre_rijal_v1"
        ):
            flags.append("active_isnad_missing_from_approved_split")
            active_isnad_missing += 1
        website_english_missing = any(
            not _plain_website_english(str(remote.get("english_text") or ""))
            and not (
                str(edge.get("review_classification") or "")
                == "website_field_anomaly"
                and not _ARABIC_CHAR_RE.search(str(remote.get("arabic_text") or ""))
                and _plain_website_english(str(remote.get("arabic_text") or ""))
            )
            for edge, remote in zip(local_edges, remotes)
        )
        if website_english_missing:
            flags.append("website_translation_missing")
            missing_website_english += 1
        if local_id not in website_translations:
            flags.append("published_website_translation_missing")
            missing_published_translation += 1
        if flags:
            issues.append(
                {
                    "public_id": hadith.public_id,
                    "sequence_in_book": hadith.sequence_in_book,
                    "printed_number": hadith.printed_number,
                    "website_paths": paths,
                    "relations": relations,
                    "displayed_arabic_coverage": round(coverage, 6),
                    "display_uses_approved_boundary": local_id in approved_boundaries,
                    "flags": flags,
                }
            )

    reviewed_local_only_ids = reviewed_local_only_ids or set()
    local_only_issues = [
        {
            "public_id": row.public_id,
            "sequence_in_book": row.sequence_in_book,
            "printed_number": row.printed_number,
            "flags": ["local_record_has_no_standalone_website_witness"],
        }
        for row in unaccounted_local
        if row.id not in reviewed_local_only_ids
    ]
    issues.extend(local_only_issues)
    issues.sort(key=lambda row: int(row["sequence_in_book"]))
    boundary_flags = {
        "website_arabic_covers_less_than_90_percent",
        "non_one_to_one_record_boundary",
        "active_isnad_missing_from_approved_split",
        "local_record_has_no_standalone_website_witness",
    }
    translation_flags = {
        "website_translation_missing",
        "published_website_translation_missing",
    }
    boundary_blockers = {
        str(row["public_id"])
        for row in issues
        if boundary_flags.intersection(row["flags"])
    }
    translation_blockers = {
        str(row["public_id"])
        for row in issues
        if translation_flags.intersection(row["flags"])
    }
    blocking_records = len({str(row["public_id"]) for row in issues})
    return {
        "minimum_displayed_arabic_coverage": minimum_coverage,
        "summary": {
            "blocking_records": blocking_records,
            "mapped_records_below_90_percent": coverage_below_90,
            "mapped_records_below_75_percent": coverage_below_75,
            "mapped_records_below_50_percent": coverage_below_50,
            "non_one_to_one_records": non_one_to_one,
            "local_only_records": len(unaccounted_local),
            "reviewed_local_only_records": len(unaccounted_local) - len(local_only_issues),
            "unreviewed_local_only_records": len(local_only_issues),
            "approved_splits_missing_detectable_isnad": active_isnad_missing,
            "records_missing_website_english": missing_website_english,
            "records_missing_published_website_translation": missing_published_translation,
            "boundary_blocking_records": len(boundary_blockers),
            "translation_blocking_records": len(translation_blockers),
            "rijal_ready": not boundary_blockers,
            "publication_ready": blocking_records == 0,
        },
        "issues": issues,
    }


def _plain_website_english(value: str | None) -> str:
    if not value:
        return ""
    return clean_ws(BeautifulSoup(value, "lxml").get_text(" ", strip=True))


def _plain_website_arabic(value: str | None) -> str:
    text = clean_ws(value)
    text = re.sub(
        r"^\s*`?\s*[0-9\u0660-\u0669\u06f0-\u06f9]+\s*[-.\u2013\u2014]\s*",
        "",
        text,
        count=1,
    )
    return text if _ARABIC_CHAR_RE.search(text) else ""


def extract_website_matn(
    website_english: str,
    *,
    existing_matn_candidates: list[str] | None = None,
) -> tuple[str, str]:
    """Return a matn-oriented excerpt made only from rendered website text.

    A previously split translation may locate the boundary, but its wording is
    accepted only when it occurs verbatim in the rendered website paragraph.
    This makes the website authoritative while avoiding duplicated English
    isnads in the reader where a verified boundary is already known.
    """

    full = _plain_website_english(website_english)
    if not full:
        return "", "empty"

    candidates = sorted(
        {
            _plain_website_english(candidate)
            for candidate in existing_matn_candidates or []
            if _plain_website_english(candidate)
        },
        key=len,
        reverse=True,
    )
    for candidate in candidates:
        if len(candidate) < 20:
            continue
        index = full.find(candidate)
        if index >= 0:
            return full[index:], "exact_existing_boundary"

    without_index = re.sub(r"^\s*\d+\s*[.]\s*", "", full, count=1)
    marker = re.search(
        r"\b(?:who|which)\s+(?:has\s+)?(?:said|stated|narrated)"
        r"(?:\s+that)?(?:\s+the)?(?:\s+following)?\s*:\s*",
        without_index,
        re.IGNORECASE,
    )
    if marker is not None and marker.end() < len(without_index):
        return without_index[marker.end() :].strip(), "narration_marker"
    return without_index, "full_fallback"


def _website_inventory_sha256(inventory: dict[str, Any]) -> str:
    return _sha256(json.dumps(inventory, ensure_ascii=False, sort_keys=True))


def import_website_english(
    db: Session,
    *,
    inventory: dict[str, Any],
    audit: dict[str, Any],
    dry_run: bool = True,
) -> WebsiteEnglishImportStats:
    """Publish rendered English for reviewed complete-report website relations."""

    stats = WebsiteEnglishImportStats()
    corpus = _corpus_from_inventory(inventory)
    inventory_sha256 = _website_inventory_sha256(inventory)
    if audit.get("inventory_sha256") != inventory_sha256:
        raise ValueError("Website audit does not belong to the supplied inventory")

    remote_by_path = {
        str(row["path"]): row for row in _inventory_rows(inventory)
    }
    chapter_hash_by_path = {
        str(row["path"]): str(chapter.get("page_sha256") or "")
        for chapter in inventory.get("chapters", [])
        for row in chapter.get("rows", [])
    }
    edges = list(audit.get("confirmed_relations", []))
    stats.considered = len(edges)

    book = db.execute(
        select(Book).where(Book.source_book_id == corpus.source_book_id)
    ).scalar_one()
    hadiths = list(
        db.execute(select(Hadith).where(Hadith.book_id == book.id)).scalars()
    )
    hadith_by_id = {hadith.id: hadith for hadith in hadiths}
    translations = list(
        db.execute(
            select(HadithTranslation)
            .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
            .where(Hadith.book_id == book.id, HadithTranslation.language == "en")
        ).scalars()
    )
    translations_by_hadith: dict[int, list[HadithTranslation]] = defaultdict(list)
    website_translation_by_hadith: dict[int, HadithTranslation] = {}
    for translation in translations:
        translations_by_hadith[translation.hadith_id].append(translation)
        if translation.translation_version == WEBSITE_TRANSLATION_VERSION:
            website_translation_by_hadith[translation.hadith_id] = translation

    version_rank = {
        WEBSITE_TRANSLATION_VERSION: 0,
        "thaqalayn_live_v1": 1,
        "matn_en_v1": 2,
    }
    minimum_score = float(audit.get("minimum_arabic_score", 0.88))

    remote_order = {
        str(row["path"]): index for index, row in enumerate(_inventory_rows(inventory))
    }
    edges_by_local: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        edges_by_local[int(edge["local_id"])].append(edge)

    for local_id, local_edges in edges_by_local.items():
        relations = {str(edge.get("relation")) for edge in local_edges}
        if relations == {"one_to_one"} and len(local_edges) == 1:
            pass
        elif relations == {"website_splits_local"}:
            pass
        elif relations == {"website_continuation"}:
            pass
        elif relations == {"website_field_anomaly"} and len(local_edges) == 1:
            pass
        else:
            stats.skipped_non_one_to_one += len(local_edges)
            continue
        local_edges.sort(key=lambda edge: remote_order[str(edge["website_path"])])
        edge = local_edges[0]
        hadith = hadith_by_id.get(local_id)
        paths = [str(item["website_path"]) for item in local_edges]
        remotes = [remote_by_path.get(path) for path in paths]
        if hadith is None or any(remote is None for remote in remotes):
            stats.errors.append(f"Missing local/website row for {paths[0]}")
            continue
        typed_remotes = [remote for remote in remotes if remote is not None]
        path = paths[0]
        remote = typed_remotes[0]

        website_parts = []
        for item, remote_row in zip(local_edges, typed_remotes):
            english_source = str(remote_row.get("english_text") or "")
            if (
                not english_source
                and item.get("review_classification") == "website_field_anomaly"
                and not _ARABIC_CHAR_RE.search(str(remote_row.get("arabic_text") or ""))
            ):
                english_source = str(remote_row.get("arabic_text") or "")
            part = _plain_website_english(english_source)
            if part:
                website_parts.append(part)
        website_full = "\n\n".join(website_parts)
        if not website_full:
            stats.skipped_missing_english += len(local_edges)
            continue

        scores = [
            _text_score(hadith, str(remote_row.get("arabic_text") or ""))
            for remote_row in typed_remotes
        ]
        verified_edges = all(
            score_value >= minimum_score or item.get("method") == "manual_review"
            for item, score_value in zip(local_edges, scores)
        )
        if not verified_edges:
            stats.skipped_stale_arabic_match += len(local_edges)
            continue
        score = min(scores, default=0.0)

        prior_rows = sorted(
            translations_by_hadith.get(hadith.id, []),
            key=lambda row: version_rank.get(row.translation_version, 99),
        )
        translator = next(
            (
                str((row.provenance_json or {}).get("translator")).strip()
                for row in prior_rows
                if (row.provenance_json or {}).get("translator")
            ),
            corpus.translator,
        )
        if not translator:
            stats.skipped_unknown_translator += 1
            continue

        matn_english, boundary_method = extract_website_matn(
            website_full,
            existing_matn_candidates=[
                row.matn_translation or ""
                for row in prior_rows
                if row.translation_version != WEBSITE_TRANSLATION_VERSION
            ],
        )
        if boundary_method == "exact_existing_boundary":
            stats.boundary_exact += 1
        elif boundary_method == "narration_marker":
            stats.boundary_marker += 1
        else:
            stats.boundary_full_fallback += 1

        provenance = {
            "source": "thaqalayn-website",
            "source_url": f"{BASE_URL}{path}",
            "chapter_url": f"{BASE_URL}{remote['chapter_path']}",
            "website_path": path,
            "website_paths": paths,
            "volume": int(remote["volume"]),
            "kitab_id": int(remote["kitab_id"]),
            "chapter_id": int(remote["chapter_id"]),
            "number_in_chapter": int(remote["number_in_chapter"]),
            "translator": translator,
            "translator_attribution": (
                "inherited-upstream-metadata"
                if any(
                    (row.provenance_json or {}).get("translator") == translator
                    for row in prior_rows
                )
                else "thaqalayn-book-page"
            ),
            "translation_classification": "external_source_normalized",
            "source_english_sha256": sha256_text(website_full),
            "source_website_arabic_sha256": str(remote.get("arabic_sha256") or ""),
            "source_website_arabic_sha256s": [
                str(remote_row.get("arabic_sha256") or "")
                for remote_row in typed_remotes
            ],
            "source_chapter_page_sha256": chapter_hash_by_path.get(path, ""),
            "source_inventory_sha256": inventory_sha256,
            "source_inventory_fetched_at": inventory.get("fetched_at"),
            "match_score": round(score, 6),
            "match_method": edge.get("method"),
            "matcher_version": WEBSITE_QA_VERSION,
            "matn_boundary_method": boundary_method,
        }
        values = {
            "source_full_sha256": sha256_text(hadith.full_text_raw),
            "source_isnad_sha256": (
                sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
            ),
            "source_matn_sha256": sha256_text(hadith.matn_raw),
            "rendered_isnad_en": None,
            "matn_translation": matn_english,
            "full_translation": website_full,
            "status": "published",
            "risk_level": "green",
            "risk_flags": [],
            "provider": WEBSITE_PROVIDER,
            "model": re.sub(r"[^a-z0-9]+", "-", translator.casefold()).strip("-"),
            "prompt_version": WEBSITE_QA_VERSION,
            "glossary_version": None,
            "qa_version": WEBSITE_QA_VERSION,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_estimate_usd": 0.0,
            "provenance_json": provenance,
        }
        translation = website_translation_by_hadith.get(hadith.id)
        if translation is None:
            stats.created += 1
            if not dry_run:
                translation = HadithTranslation(
                    hadith_id=hadith.id,
                    language="en",
                    translation_version=WEBSITE_TRANSLATION_VERSION,
                    **values,
                )
                db.add(translation)
        else:
            unchanged = all(getattr(translation, key) == value for key, value in values.items())
            if unchanged:
                stats.unchanged += 1
            else:
                stats.updated += 1
                if not dry_run:
                    for key, value in values.items():
                        setattr(translation, key, value)
        stats.imported += 1

    if not dry_run:
        db.flush()
    return stats


def _combined_similarity(local_rows: list[Hadith], remote_rows: list[dict[str, Any]]) -> float:
    local = "".join(match_norm(row.full_text_raw) for row in local_rows)
    remote = "".join(match_norm(str(row["arabic_text"])) for row in remote_rows)
    if not local or not remote:
        return 0.0
    if local in remote or remote in local:
        return min(len(local), len(remote)) / max(len(local), len(remote))
    return SequenceMatcher(None, local, remote, autojunk=False).ratio()


def _add_residual_split_candidates(
    *,
    local_rows: list[Hadith],
    remote_rows: list[dict[str, Any]],
    candidates: dict[tuple[int, str], dict[str, Any]],
    min_score: float,
) -> None:
    """Find verified one-to-many boundaries missed by one-edge seed maps.

    A structure map can store only one website route per local row. Long
    reports are sometimes divided into many rendered routes, so a second
    indexed pass is needed after the ordinary one-to-one links are known.
    Eight-character Arabic samples nominate a candidate; the normal Arabic
    score remains the acceptance gate.
    """

    local_by_id = {row.id: row for row in local_rows}
    local_position = {row.id: index for index, row in enumerate(local_rows)}
    remote_by_path = {str(row["path"]): row for row in remote_rows}
    accounted_local = {local_id for local_id, _ in candidates}
    accounted_remote = {path for _, path in candidates}

    local_grams: dict[int, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    for hadith in local_rows:
        volume = int(hadith.volume_start or 0)
        for text in {
            _cached_edition_norm(hadith.full_text_raw),
            _cached_edition_norm(hadith.matn_raw),
        }:
            for index in range(0, max(0, len(text) - 7), 4):
                local_grams[volume][text[index : index + 8]].add(hadith.id)

    def best_local(remote: dict[str, Any]) -> tuple[Hadith, float] | None:
        text = _cached_edition_norm(str(remote.get("arabic_text") or ""))
        counts: Counter[int] = Counter()
        gram_index = local_grams[int(remote["volume"])]
        for index in range(max(0, len(text) - 7)):
            counts.update(gram_index.get(text[index : index + 8], ()))
        if not counts:
            return None
        ranked = counts.most_common(2)
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            return None
        hadith = local_by_id[ranked[0][0]]
        score = _text_score(hadith, str(remote.get("arabic_text") or ""))
        return (hadith, score) if score >= min_score else None

    for remote in remote_rows:
        path = str(remote["path"])
        if path in accounted_remote:
            continue
        result = best_local(remote)
        if result is None:
            continue
        hadith, score = result
        candidates[(hadith.id, path)] = {
            "local_id": hadith.id,
            "public_id": hadith.public_id,
            "website_path": path,
            "method": "indexed_split_arabic",
            "score": round(score, 6),
        }

    # The inverse pass catches local subdivisions of an already-linked website
    # route. Keep the same Arabic gate and uniqueness rule.
    remote_grams: dict[int, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for remote in remote_rows:
        text = _cached_edition_norm(str(remote.get("arabic_text") or ""))
        for index in range(0, max(0, len(text) - 7), 4):
            remote_grams[int(remote["volume"])][text[index : index + 8]].add(
                str(remote["path"])
            )

    for hadith in local_rows:
        if hadith.id in accounted_local:
            continue
        counts: Counter[str] = Counter()
        gram_index = remote_grams[int(hadith.volume_start or 0)]
        for text in {
            _cached_edition_norm(hadith.full_text_raw),
            _cached_edition_norm(hadith.matn_raw),
        }:
            for index in range(max(0, len(text) - 7)):
                counts.update(gram_index.get(text[index : index + 8], ()))
        if not counts:
            continue
        ranked = counts.most_common(2)
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            continue
        path = ranked[0][0]
        anchor_ids = {
            local_id
            for local_id, candidate_path in candidates
            if candidate_path == path
        }
        # A website report may genuinely span adjacent local fragments. A
        # repeated report hundreds of rows later is a separate occurrence and
        # must retain its own source location and chain for rijal work.
        if not anchor_ids or min(
            abs(local_position[hadith.id] - local_position[anchor_id])
            for anchor_id in anchor_ids
        ) > 2:
            continue
        score = _text_score(hadith, str(remote_by_path[path].get("arabic_text") or ""))
        if score < min_score:
            continue
        candidates[(hadith.id, path)] = {
            "local_id": hadith.id,
            "public_id": hadith.public_id,
            "website_path": path,
            "method": "indexed_combined_arabic",
            "score": round(score, 6),
        }


def audit_thaqalayn_website(
    db: Session,
    *,
    inventory: dict[str, Any],
    min_score: float = 0.88,
    review_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify local rows against the website and report both directions."""

    corpus = _corpus_from_inventory(inventory)
    inventory_sha256 = _website_inventory_sha256(inventory)
    if review_manifest is not None:
        if review_manifest.get("corpus_key") != corpus.key:
            raise ValueError("Review manifest corpus does not match the inventory")
        if review_manifest.get("inventory_sha256") != inventory_sha256:
            raise ValueError("Review manifest does not belong to the supplied inventory")
    book = db.execute(
        select(Book).where(Book.source_book_id == corpus.source_book_id)
    ).scalar_one()
    local_rows = list(
        db.execute(
            select(Hadith)
            .where(
                Hadith.book_id == book.id,
                Hadith.review_status != "rejected_non_hadith_fragment",
            )
            .order_by(Hadith.sequence_in_book)
        ).scalars()
    )
    local_by_id = {row.id: row for row in local_rows}
    local_by_public = {row.public_id: row for row in local_rows}
    remote_rows = _inventory_rows(inventory)
    remote_by_path = {str(row["path"]): row for row in remote_rows}
    remote_index = {str(row["path"]): index for index, row in enumerate(remote_rows)}
    local_index = {row.id: index for index, row in enumerate(local_rows)}

    candidates: dict[tuple[int, str], dict[str, Any]] = {}

    def consider(hadith: Hadith, path: str | None, method: str) -> None:
        if path is None or path not in remote_by_path:
            return
        score = _text_score(hadith, str(remote_by_path[path]["arabic_text"]))
        key = (hadith.id, path)
        old = candidates.get(key)
        if score >= min_score and (old is None or score > old["score"]):
            candidates[key] = {
                "local_id": hadith.id,
                "public_id": hadith.public_id,
                "website_path": path,
                "method": method,
                "score": round(score, 6),
            }

    maps = list(
        db.execute(
            select(ThaqalaynStructureMap)
            .join(Hadith, Hadith.id == ThaqalaynStructureMap.hadith_id)
            .where(
                Hadith.book_id == book.id,
                ThaqalaynStructureMap.mapping_status == "matched",
            )
        ).scalars()
    )
    for mapping in maps:
        hadith = local_by_id.get(mapping.hadith_id)
        if hadith is not None:
            consider(hadith, canonical_hadith_path(mapping.thaqalayn_url), "structure_map")

    translations = list(
        db.execute(
            select(HadithTranslation)
            .join(Hadith, Hadith.id == HadithTranslation.hadith_id)
            .where(Hadith.book_id == book.id, HadithTranslation.status == "published")
        ).scalars()
    )
    for translation in translations:
        hadith = local_by_id.get(translation.hadith_id)
        if hadith is None:
            continue
        provenance = translation.provenance_json or {}
        path = canonical_hadith_path(
            provenance.get("source_url") or provenance.get("url")
        )
        consider(hadith, path, "translation_provenance")

    # Faqih's printed global narration number is present independently in
    # both editions. It remains stable even when one edition appends a juristic
    # comment to the report or expands an honorific, so it is a stronger key
    # than proportional text overlap for those rows.
    remote_by_printed_number: dict[tuple[int, int], list[str]] = defaultdict(list)
    for path, row in remote_by_path.items():
        number = _website_global_number(row)
        if number is not None:
            remote_by_printed_number[(int(row["volume"]), number)].append(path)
    local_printed_counts = Counter(
        (int(hadith.volume_start or 0), number)
        for hadith in local_rows
        if (number := _digits_only(hadith.printed_number)) is not None
    )
    for hadith in local_rows:
        number = _digits_only(hadith.printed_number)
        if number is None:
            continue
        if local_printed_counts[(int(hadith.volume_start or 0), number)] != 1:
            continue
        paths = remote_by_printed_number.get(
            (int(hadith.volume_start or 0), number), []
        )
        if len(paths) != 1:
            continue
        path = paths[0]
        key = (hadith.id, path)
        if key in candidates:
            continue
        remote_arabic = str(remote_by_path[path].get("arabic_text") or "")
        if not _ARABIC_CHAR_RE.search(remote_arabic):
            continue
        # Printed numbering is useful for proposing a route, but local parser
        # number corruption can otherwise displace the genuine Arabic match.
        # Completeness evidence must meet the same Arabic gate as every other
        # confirmed relation.
        consider(hadith, path, "printed_number_rekey")

    local_with_edges = {local_id for local_id, _ in candidates}
    remote_with_edges = {path for _, path in candidates}

    remote_exact: dict[str, list[str]] = defaultdict(list)
    for path, row in remote_by_path.items():
        remote_exact[match_norm(str(row["arabic_text"]))].append(path)
    for hadith in local_rows:
        if hadith.id in local_with_edges:
            continue
        norms = {match_norm(hadith.full_text_raw), match_norm(hadith.matn_raw)} - {""}
        paths = {
            path
            for norm in norms
            for path in remote_exact.get(norm, [])
            if path not in remote_with_edges
        }
        if len(paths) == 1:
            consider(hadith, next(iter(paths)), "unique_exact_arabic")

    # Route numbers are presentation details, not durable identities. When a
    # website migration renumbers thousands of otherwise unchanged reports,
    # seed the content-indexed matches before the bounded SequenceMatcher
    # fallback. This keeps the audit near-linear and leaves only genuine text
    # differences for the more expensive ordered-window pass.
    if corpus.key == FAQIH_CORPUS.key:
        _add_residual_split_candidates(
            local_rows=local_rows,
            remote_rows=remote_rows,
            candidates=candidates,
            min_score=min_score,
        )

    # Most source-edition differences are honorific expansions, footnotes, or
    # a short compiler comment attached to one side. Match the remaining rows
    # monotonically inside each printed volume, keeping a bounded window and
    # refusing tied candidates so repeated formulae never become silent links.
    claimed_local = {local_id for local_id, _ in candidates}
    claimed_remote = {path for _, path in candidates}
    paths_by_local: dict[int, list[str]] = defaultdict(list)
    for local_id, path in candidates:
        paths_by_local[local_id].append(path)
    for volume in sorted({int(row.volume_start or 0) for row in local_rows}):
        local_volume = [
            row
            for row in local_rows
            if int(row.volume_start or 0) == volume
        ]
        remote_volume = [
            row for row in remote_rows if int(row["volume"]) == volume
        ]
        remote_positions = {
            str(row["path"]): index for index, row in enumerate(remote_volume)
        }
        cursor = 0
        for hadith in local_volume:
            if hadith.id in claimed_local:
                linked_positions = [
                    remote_positions[path]
                    for path in paths_by_local.get(hadith.id, [])
                    if path in remote_positions
                ]
                if linked_positions:
                    cursor = max(cursor, max(linked_positions) + 1)
                continue
            start = max(0, cursor - 48)
            end = min(len(remote_volume), cursor + 128)
            scored = sorted(
                (
                    (_text_score(hadith, str(remote["arabic_text"])), remote)
                    for remote in remote_volume[start:end]
                    if str(remote["path"]) not in claimed_remote
                ),
                key=lambda item: (
                    item[0],
                    -abs(remote_positions[str(item[1]["path"])] - cursor),
                ),
                reverse=True,
            )
            if not scored or scored[0][0] < min_score:
                continue
            best_score, best = scored[0]
            if len(scored) > 1 and abs(best_score - scored[1][0]) < 0.01:
                continue
            path = str(best["path"])
            consider(hadith, path, "windowed_website_arabic")
            claimed_local.add(hadith.id)
            claimed_remote.add(path)
            paths_by_local[hadith.id].append(path)
            cursor = max(cursor, remote_positions[path] + 1)

    # Promote tightly bounded lower-similarity gaps when both editions contain
    # the same small number of rows in the same order. This captures benign
    # compiler-comment and honorific differences while retaining the anchors
    # and scores needed to audit every decision later.
    for _ in range(4):
        local_degree = Counter(local_id for local_id, _ in candidates)
        remote_degree = Counter(path for _, path in candidates)
        anchors = [
            value
            for key, value in candidates.items()
            if local_degree[key[0]] == 1 and remote_degree[key[1]] == 1
        ]
        anchors.sort(key=lambda edge: local_index[edge["local_id"]])
        additions: list[tuple[Hadith, dict[str, Any], float]] = []
        accounted_local_ids = {local_id for local_id, _ in candidates}
        accounted_remote_paths = {path for _, path in candidates}
        for left, right in zip(anchors, anchors[1:]):
            left_local = local_by_id[left["local_id"]]
            right_local = local_by_id[right["local_id"]]
            left_remote = remote_by_path[left["website_path"]]
            right_remote = remote_by_path[right["website_path"]]
            if left_local.volume_start != right_local.volume_start:
                continue
            if int(left_remote["volume"]) != int(right_remote["volume"]):
                continue
            li, ri = local_index[left_local.id], local_index[right_local.id]
            lw, rw = remote_index[left["website_path"]], remote_index[right["website_path"]]
            if ri <= li or rw <= lw:
                continue
            local_gap = [
                row
                for row in local_rows[li + 1 : ri]
                if row.id not in accounted_local_ids
            ]
            remote_gap = [
                row
                for row in remote_rows[lw + 1 : rw]
                if str(row["path"]) not in accounted_remote_paths
            ]
            if not local_gap or len(local_gap) != len(remote_gap) or len(local_gap) > 8:
                continue
            combined = _combined_similarity(local_gap, remote_gap)
            pair_scores = [
                _text_score(local, str(remote["arabic_text"]))
                for local, remote in zip(local_gap, remote_gap)
            ]
            threshold = 0.7 if len(local_gap) == 1 else 0.76
            if combined < threshold or min(pair_scores, default=0.0) < 0.55:
                continue
            additions.extend(
                (local, remote, score)
                for local, remote, score in zip(local_gap, remote_gap, pair_scores)
            )
        if not additions:
            break
        for local, remote, score in additions:
            key = (local.id, str(remote["path"]))
            if key in candidates:
                continue
            candidates[key] = {
                "local_id": local.id,
                "public_id": local.public_id,
                "website_path": str(remote["path"]),
                "method": "bounded_ordered_arabic",
                "score": round(score, 6),
            }

    for exclusion in (review_manifest or {}).get("excluded_relations", []):
        public_id = str(exclusion["public_id"])
        path = str(exclusion["website_path"])
        hadith = local_by_public.get(public_id)
        remote = remote_by_path.get(path)
        if hadith is None or remote is None:
            raise ValueError(f"Unknown excluded website relation: {public_id} -> {path}")
        if exclusion.get("local_arabic_sha256") != sha256_text(
            clean_ws(hadith.full_text_raw)
        ):
            raise ValueError(f"Stale local Arabic exclusion evidence for {public_id}")
        if exclusion.get("website_arabic_sha256") != str(
            remote.get("arabic_sha256") or ""
        ):
            raise ValueError(f"Stale website exclusion evidence for {path}")
        if candidates.pop((hadith.id, path), None) is None:
            raise ValueError(f"Excluded relation is no longer proposed: {public_id} -> {path}")

    for manual in (review_manifest or {}).get("manual_relations", []):
        public_id = str(manual["public_id"])
        path = str(manual["website_path"])
        hadith = local_by_public.get(public_id)
        remote = remote_by_path.get(path)
        if hadith is None or remote is None:
            raise ValueError(f"Unknown manual website relation: {public_id} -> {path}")
        local_sha256 = sha256_text(clean_ws(hadith.full_text_raw))
        remote_sha256 = str(remote.get("arabic_sha256") or "")
        if manual.get("local_arabic_sha256") != local_sha256:
            raise ValueError(f"Stale local Arabic evidence for {public_id}")
        if manual.get("website_arabic_sha256") != remote_sha256:
            raise ValueError(f"Stale website evidence for {path}")
        candidates[(hadith.id, path)] = {
            "local_id": hadith.id,
            "public_id": hadith.public_id,
            "website_path": path,
            "method": "manual_review",
            "score": round(_text_score(hadith, str(remote.get("arabic_text") or "")), 6),
            "review_classification": str(manual["classification"]),
            "review_note": str(manual["note"]),
        }

    edges = sorted(
        candidates.values(),
        key=lambda row: (local_by_id[row["local_id"]].sequence_in_book, row["website_path"]),
    )
    local_paths: dict[int, set[str]] = defaultdict(set)
    remote_locals: dict[str, set[int]] = defaultdict(set)
    for edge in edges:
        local_paths[edge["local_id"]].add(edge["website_path"])
        remote_locals[edge["website_path"]].add(edge["local_id"])

    relation_counts = Counter()
    for edge in edges:
        local_degree = len(local_paths[edge["local_id"]])
        remote_degree = len(remote_locals[edge["website_path"]])
        if local_degree == 1 and remote_degree == 1:
            relation = "one_to_one"
        elif local_degree > 1 and remote_degree == 1:
            relation = "website_splits_local"
        elif local_degree == 1 and remote_degree > 1:
            relation = "website_combines_local"
        else:
            relation = "many_to_many_review"
        review_classification = str(edge.get("review_classification") or "")
        if review_classification in {
            "website_continuation",
            "partial_website_continuation",
            "duplicate_website_occurrence",
            "independent_unnumbered_report",
            "website_field_anomaly",
        }:
            relation = review_classification
        elif review_classification == "partial_overlap":
            relation = "partial_website_continuation"
        edge["relation"] = relation
        relation_counts[relation] += 1

    accounted_local = set(local_paths)
    accounted_remote = set(remote_locals)
    unaccounted_local = [row for row in local_rows if row.id not in accounted_local]
    unaccounted_remote = [row for row in remote_rows if str(row["path"]) not in accounted_remote]

    # Small gaps bounded by monotonic one-to-one anchors are useful split/merge
    # review units. They are candidates only and never count as confirmed.
    anchors = [
        edge
        for edge in edges
        if edge["relation"] == "one_to_one"
    ]
    anchors.sort(key=lambda edge: local_by_id[edge["local_id"]].sequence_in_book)
    candidate_blocks: list[dict[str, Any]] = []
    for left, right in zip(anchors, anchors[1:]):
        left_local = local_by_id[left["local_id"]]
        right_local = local_by_id[right["local_id"]]
        left_remote = remote_by_path[left["website_path"]]
        right_remote = remote_by_path[right["website_path"]]
        if left_local.volume_start != right_local.volume_start:
            continue
        if int(left_remote["volume"]) != int(right_remote["volume"]):
            continue
        li, ri = local_index[left_local.id], local_index[right_local.id]
        lw, rw = remote_index[left["website_path"]], remote_index[right["website_path"]]
        if ri <= li or rw <= lw:
            continue
        local_gap = [row for row in local_rows[li + 1 : ri] if row.id not in accounted_local]
        remote_gap = [
            row
            for row in remote_rows[lw + 1 : rw]
            if str(row["path"]) not in accounted_remote
        ]
        if not local_gap or not remote_gap or len(local_gap) > 8 or len(remote_gap) > 8:
            continue
        similarity = _combined_similarity(local_gap, remote_gap)
        if similarity < 0.7:
            continue
        candidate_blocks.append(
            {
                "left_anchor": left["public_id"],
                "right_anchor": right["public_id"],
                "local_public_ids": [row.public_id for row in local_gap],
                "website_paths": [str(row["path"]) for row in remote_gap],
                "local_count": len(local_gap),
                "website_count": len(remote_gap),
                "combined_similarity": round(similarity, 6),
            }
        )

    by_volume_local = Counter(int(row.volume_start or 0) for row in local_rows)
    by_volume_remote = Counter(int(row["volume"]) for row in remote_rows)
    method_counts = Counter(edge["method"] for edge in edges)
    candidate_local_ids = {
        public_id
        for block in candidate_blocks
        for public_id in block["local_public_ids"]
    }
    candidate_remote_paths = {
        path
        for block in candidate_blocks
        for path in block["website_paths"]
    }
    website_numbered_gaps = [
        row for row in unaccounted_remote if _website_global_number(row) is not None
    ]
    website_nonindependent = [
        row for row in unaccounted_remote if _website_global_number(row) is None
    ]
    local_keys = [row.public_id for row in unaccounted_local]
    local_evidence_sha256 = _local_only_evidence_sha256(unaccounted_local)
    website_nonindependent_keys = [str(row["path"]) for row in website_nonindependent]
    numbered_gap_keys = [str(row["path"]) for row in website_numbered_gaps]
    locks = (review_manifest or {}).get("expected_residuals", {})
    local_lock_match = (
        bool(review_manifest)
        and locks.get("local_only_count") == len(local_keys)
        and locks.get("local_only_sha256") == _key_list_sha256(local_keys)
        and locks.get("local_only_evidence_sha256") == local_evidence_sha256
    )
    website_lock_match = bool(review_manifest) and locks.get(
        "website_nonindependent_count"
    ) == len(website_nonindependent_keys) and locks.get(
        "website_nonindependent_sha256"
    ) == _key_list_sha256(website_nonindependent_keys)
    numbered_gap_lock_match = not numbered_gap_keys or (
        bool(review_manifest)
        and locks.get("website_numbered_gap_count") == len(numbered_gap_keys)
        and locks.get("website_numbered_gap_sha256")
        == _key_list_sha256(numbered_gap_keys)
    )
    claim_ready = (
        local_lock_match
        and website_lock_match
        and numbered_gap_lock_match
        and not website_numbered_gaps
    )
    publication_quality = _publication_quality(
        db,
        local_rows=local_rows,
        remote_by_path=remote_by_path,
        edges=edges,
        unaccounted_local=unaccounted_local,
        reviewed_local_only_ids=(
            {row.id for row in unaccounted_local} if local_lock_match else set()
        ),
    )

    result = {
        "schema_version": corpus.schema_version,
        "corpus_key": corpus.key,
        "title": corpus.title,
        "source_book_id": corpus.source_book_id,
        "audited_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": BASE_URL,
        "inventory_sha256": inventory_sha256,
        "minimum_arabic_score": min_score,
        "summary": {
            "local_visible": len(local_rows),
            "website_hadiths": len(remote_rows),
            "confirmed_local": len(accounted_local),
            "confirmed_website": len(accounted_remote),
            "unaccounted_local": len(unaccounted_local),
            "unaccounted_website": len(unaccounted_remote),
            "confirmed_edges": len(edges),
            "candidate_split_merge_blocks": len(candidate_blocks),
            "candidate_local_reports": len(candidate_local_ids),
            "candidate_website_reports": len(candidate_remote_paths),
            "outside_candidates_local": len(unaccounted_local) - len(candidate_local_ids),
            "outside_candidates_website": len(unaccounted_remote) - len(candidate_remote_paths),
            "reviewed_local_only": len(unaccounted_local) if local_lock_match else 0,
            "reviewed_website_nonindependent": (
                len(website_nonindependent) if website_lock_match else 0
            ),
            "website_numbered_gaps": len(website_numbered_gaps),
            "unclassified_local": 0 if local_lock_match else len(unaccounted_local),
            "unclassified_website": (
                0 if website_lock_match else len(website_nonindependent)
            ) + (0 if numbered_gap_lock_match else len(website_numbered_gaps)),
            "claim_ready": claim_ready,
            "inventory_ready": claim_ready,
            "publication_ready": publication_quality["summary"]["publication_ready"],
            "rijal_ready": publication_quality["summary"]["rijal_ready"],
        },
        "publication_quality": publication_quality,
        "website_inventory": {
            "chapter_count": int(inventory["chapter_count"]),
            "sitemap_path_count": int(inventory["hadith_sitemap"]["path_count"]),
            "non_report_count": len(inventory.get("non_report_entries", [])),
            "anomaly_count": len(inventory.get("anomalies", [])),
        },
        "local_by_volume": dict(sorted(by_volume_local.items())),
        "website_by_volume": dict(sorted(by_volume_remote.items())),
        "method_counts": dict(sorted(method_counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "review_state": {
            "manifest_present": review_manifest is not None,
            "local_only_lock_match": local_lock_match,
            "website_nonindependent_lock_match": website_lock_match,
            "website_numbered_gap_lock_match": numbered_gap_lock_match,
            "local_only_sha256": _key_list_sha256(local_keys),
            "local_only_evidence_sha256": local_evidence_sha256,
            "website_nonindependent_sha256": _key_list_sha256(
                website_nonindependent_keys
            ),
            "website_numbered_gap_sha256": _key_list_sha256(numbered_gap_keys),
        },
        "confirmed_relations": edges,
        "candidate_split_merge_blocks": candidate_blocks,
        "unaccounted_local": [
            {
                "public_id": row.public_id,
                "volume": row.volume_start,
                "page_start": row.page_start,
                "printed_number": row.printed_number,
                "sequence_in_book": row.sequence_in_book,
            }
            for row in unaccounted_local
        ],
        "unaccounted_website": [
            {
                "path": row["path"],
                "volume": row["volume"],
                "kitab_id": row["kitab_id"],
                "chapter_id": row["chapter_id"],
                "number_in_chapter": row["number_in_chapter"],
            }
            for row in unaccounted_remote
        ],
        "website_numbered_gaps": [
            {
                "path": row["path"],
                "volume": row["volume"],
                "kitab_id": row["kitab_id"],
                "chapter_id": row["chapter_id"],
                "number_in_chapter": row["number_in_chapter"],
                "printed_number": _website_global_number(row),
            }
            for row in website_numbered_gaps
        ],
        "reviewed_local_only": [
            {
                "public_id": row.public_id,
                "classification": "local_edition_report_without_standalone_website_route",
            }
            for row in unaccounted_local
            if local_lock_match
        ],
        "reviewed_website_nonindependent": [
            {
                "path": row["path"],
                "classification": "editorial_or_subdivision_non_independent",
            }
            for row in website_nonindependent
        ],
    }
    return result


def audit_alkafi_website(
    db: Session,
    *,
    inventory: dict[str, Any],
    min_score: float = 0.88,
) -> dict[str, Any]:
    """Backward-compatible wrapper for existing Al-Kafi tooling."""

    if "corpus_key" not in inventory:
        inventory = {**inventory, "corpus_key": AL_KAFI_CORPUS.key}
    return audit_thaqalayn_website(db, inventory=inventory, min_score=min_score)


def repair_website_arabic_boundaries(
    db: Session,
    *,
    inventory: dict[str, Any],
    audit: dict[str, Any],
    chapter_path: str | None = None,
    quality_blockers_only: bool = False,
    simple_splits_only: bool = False,
    dry_run: bool = True,
) -> WebsiteBoundaryRepairStats:
    """Use rendered website Arabic to repair public record boundaries.

    The extracted full text is retained as the source-edition witness. The
    active isnad/matn fields become the clean website-bounded report. A simple
    two-report local combination is split into two stable public records.
    """

    corpus = _corpus_from_inventory(inventory)
    if corpus.key != FAQIH_CORPUS.key:
        raise ValueError("Website boundary repair is currently reviewed only for Faqih")
    if audit.get("inventory_sha256") != _website_inventory_sha256(inventory):
        raise ValueError("Website audit does not belong to the supplied inventory")

    book = db.execute(
        select(Book).where(Book.source_book_id == corpus.source_book_id)
    ).scalar_one()
    hadiths = list(
        db.execute(
            select(Hadith)
            .where(Hadith.book_id == book.id)
            .order_by(Hadith.sequence_in_book)
        ).scalars()
    )
    by_id = {row.id: row for row in hadiths}
    existing_public_ids = {row.public_id for row in hadiths}
    remote_by_path = {
        str(row["path"]): row for row in _inventory_rows(inventory)
    }
    blocker_public_ids = {
        str(issue["public_id"])
        for issue in audit.get("publication_quality", {}).get("issues", [])
        if "website_arabic_covers_less_than_90_percent" in issue.get("flags", [])
    }
    edges_by_local: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in audit.get("confirmed_relations", []):
        remote = remote_by_path.get(str(edge["website_path"]))
        chapter_matches = chapter_path is None or (
            remote and str(remote.get("chapter_path")) == chapter_path
        )
        quality_matches = (
            not quality_blockers_only
            or str(edge.get("public_id")) in blocker_public_ids
        )
        relation_matches = (
            not simple_splits_only
            or str(edge.get("relation"))
            in {"website_splits_local", "independent_unnumbered_report"}
        )
        if remote and chapter_matches and quality_matches and relation_matches:
            edges_by_local[int(edge["local_id"])].append(edge)

    stats = WebsiteBoundaryRepairStats(considered=len(edges_by_local))

    def repair_existing(hadith: Hadith, remote: dict[str, Any]) -> None:
        arabic = _plain_website_arabic(str(remote.get("arabic_text") or ""))
        if not arabic:
            raise ValueError(f"Website Arabic is empty for {remote['path']}")
        isnad, matn = split_isnad_matn(arabic)
        unchanged = hadith.isnad_raw == isnad and hadith.matn_raw == matn
        if unchanged:
            stats.unchanged += 1
            return
        stats.boundaries_repaired += 1
        if dry_run:
            return
        hadith.isnad_raw = isnad
        hadith.isnad_normalised = (
            normalise_arabic_persian(isnad) if isnad else None
        )
        hadith.matn_raw = matn
        hadith.matn_normalised = normalise_arabic_persian(matn)
        hadith.extraction_confidence = 100
        hadith.review_status = "website_boundary_approved"
        review = db.execute(
            select(HadithSplitReview).where(HadithSplitReview.hadith_id == hadith.id)
        ).scalar_one_or_none()
        values = {
            "approved_isnad_raw": isnad,
            "approved_matn_raw": matn,
            "review_status": "approved",
            "reviewer": WEBSITE_PROVIDER,
            "notes": f"Arabic boundary verified against {BASE_URL}{remote['path']}",
            "split_version": WEBSITE_QA_VERSION,
        }
        if review is None:
            db.add(HadithSplitReview(hadith_id=hadith.id, **values))
        else:
            for key, value in values.items():
                setattr(review, key, value)

    for local_id, local_edges in sorted(
        edges_by_local.items(), key=lambda item: by_id[item[0]].sequence_in_book
    ):
        hadith = by_id[local_id]
        local_edges.sort(
            key=lambda edge: int(remote_by_path[str(edge["website_path"])]["number_in_chapter"])
        )
        relations = {str(edge.get("relation")) for edge in local_edges}
        if relations == {"one_to_one"} and len(local_edges) == 1:
            if simple_splits_only:
                stats.skipped_complex_relations += 1
                continue
            repair_existing(hadith, remote_by_path[str(local_edges[0]["website_path"])])
            continue
        if quality_blockers_only:
            stats.skipped_complex_relations += 1
            continue
        split_relation = relations in (
            {"website_splits_local"},
            {"independent_unnumbered_report"},
        )
        if not split_relation or len(local_edges) != 2:
            stats.skipped_complex_relations += 1
            continue

        first_remote = remote_by_path[str(local_edges[0]["website_path"])]
        second_remote = remote_by_path[str(local_edges[1]["website_path"])]
        first_number = _website_global_number(first_remote)
        second_number = _website_global_number(second_remote)
        unnumbered_reviewed = (
            relations == {"independent_unnumbered_report"}
            and first_number is not None
            and second_number is None
        )
        if first_number is None or (
            not unnumbered_reviewed and second_number != first_number + 1
        ):
            stats.skipped_complex_relations += 1
            continue
        repair_existing(hadith, first_remote)
        public_id = (
            "faqih-web-" + str(second_number)
            if second_number is not None
            else "faqih-web-" + str(second_remote["path"]).removeprefix("/hadith/").replace("/", "-")
        )
        if public_id in existing_public_ids:
            stats.unchanged += 1
            continue
        stats.split_records_created += 1
        if dry_run:
            continue

        target = hadith.sequence_in_book + 1
        db.execute(
            update(Hadith)
            .where(Hadith.book_id == book.id, Hadith.sequence_in_book >= target)
            .values(sequence_in_book=Hadith.sequence_in_book + 10_000)
        )
        db.execute(
            update(Hadith)
            .where(Hadith.book_id == book.id, Hadith.sequence_in_book >= target + 10_000)
            .values(sequence_in_book=Hadith.sequence_in_book - 9_999)
        )
        arabic = _plain_website_arabic(str(second_remote.get("arabic_text") or ""))
        normalized = normalise_arabic_persian(arabic)
        created = Hadith(
            public_id=public_id,
            book_id=book.id,
            page_start_id=hadith.page_start_id,
            page_end_id=hadith.page_end_id,
            sequence_in_book=target,
            sequence_in_page=hadith.sequence_in_page + 1,
            printed_number=(str(second_number) if second_number is not None else None),
            volume_start=hadith.volume_start,
            volume_end=hadith.volume_end,
            page_start=hadith.page_start,
            page_end=hadith.page_end,
            section_title=hadith.section_title,
            full_text_raw=arabic,
            full_text_normalised=normalized,
            isnad_raw=None,
            isnad_normalised=None,
            matn_raw=arabic,
            matn_normalised=normalized,
            footnotes_json=None,
            source_url=f"{BASE_URL}{second_remote['path']}",
            extraction_method=WEBSITE_QA_VERSION,
            extraction_confidence=100,
            review_status="website_boundary_approved",
        )
        db.add(created)
        db.flush()
        existing_public_ids.add(public_id)

    if not dry_run:
        db.flush()
    return stats


def import_website_numbered_gaps(
    db: Session,
    *,
    inventory: dict[str, Any],
    audit: dict[str, Any],
    dry_run: bool = True,
) -> WebsiteGapImportStats:
    """Add numbered website reports proven absent from the local edition rows."""

    corpus = _corpus_from_inventory(inventory)
    if corpus.key != FAQIH_CORPUS.key:
        raise ValueError("Numbered website gap import is currently reviewed only for Faqih")
    inventory_sha256 = _website_inventory_sha256(inventory)
    if audit.get("inventory_sha256") != inventory_sha256:
        raise ValueError("Website audit does not belong to the supplied inventory")
    review_state = audit.get("review_state") or {}
    if not all(
        review_state.get(key)
        for key in (
            "local_only_lock_match",
            "website_nonindependent_lock_match",
            "website_numbered_gap_lock_match",
        )
    ):
        raise ValueError("Website reconciliation locks are incomplete or stale")

    gaps = list(audit.get("website_numbered_gaps") or [])
    stats = WebsiteGapImportStats(considered=len(gaps))
    if not gaps:
        return stats

    book = db.execute(
        select(Book).where(Book.source_book_id == corpus.source_book_id)
    ).scalar_one()
    hadiths = list(
        db.execute(
            select(Hadith)
            .where(Hadith.book_id == book.id)
            .order_by(Hadith.sequence_in_book)
        ).scalars()
    )
    hadith_by_id = {row.id: row for row in hadiths}
    existing_public_ids = {row.public_id for row in hadiths}
    remote_rows = _inventory_rows(inventory)
    remote_by_path = {str(row["path"]): row for row in remote_rows}
    remote_index = {str(row["path"]): index for index, row in enumerate(remote_rows)}
    edge_by_path = {
        str(edge["website_path"]): edge
        for edge in audit.get("confirmed_relations", [])
        if edge.get("relation") != "partial_overlap"
    }

    planned: list[tuple[int, dict[str, Any], str]] = []
    for gap in gaps:
        path = str(gap["path"])
        remote = remote_by_path[path]
        number = int(gap["printed_number"])
        public_id = f"faqih-web-{number}"
        if public_id in existing_public_ids:
            stats.skipped_existing += 1
            continue
        position = remote_index[path]
        target = max((row.sequence_in_book for row in hadiths), default=0) + 1
        for later in remote_rows[position + 1 :]:
            edge = edge_by_path.get(str(later["path"]))
            if edge is None:
                continue
            anchor = hadith_by_id.get(int(edge["local_id"]))
            if anchor is not None:
                target = anchor.sequence_in_book
                break
        planned.append((target, remote, public_id))

    if dry_run:
        stats.created_hadiths = len(planned)
        stats.created_translations = sum(
            bool(_plain_website_english(str(remote.get("english_text") or "")))
            for _, remote, _ in planned
        )
        return stats

    for target, remote, public_id in sorted(planned, key=lambda row: row[0], reverse=True):
        db.execute(
            update(Hadith)
            .where(Hadith.book_id == book.id, Hadith.sequence_in_book >= target)
            .values(sequence_in_book=Hadith.sequence_in_book + 10_000)
        )
        db.execute(
            update(Hadith)
            .where(Hadith.book_id == book.id, Hadith.sequence_in_book >= target + 10_000)
            .values(sequence_in_book=Hadith.sequence_in_book - 9_999)
        )

        path = str(remote["path"])
        number = int(_website_global_number(remote) or 0)
        arabic = clean_ws(str(remote.get("arabic_text") or ""))
        arabic = re.sub(r"^\s*[0-9٠-٩۰-۹]+\s*[-–—.]\s*", "", arabic)
        normalized = normalise_arabic_persian(arabic)
        anchor = next(
            (
                row
                for row in hadiths
                if row.sequence_in_book >= target
                and int(row.volume_start or 0) == int(remote["volume"])
            ),
            None,
        )
        hadith = Hadith(
            public_id=public_id,
            book_id=book.id,
            sequence_in_book=target,
            sequence_in_page=1,
            printed_number=str(number),
            volume_start=int(remote["volume"]),
            volume_end=int(remote["volume"]),
            page_start=anchor.page_start if anchor else 0,
            page_end=anchor.page_start if anchor else 0,
            section_title=str(remote.get("chapter_name_en") or ""),
            full_text_raw=arabic,
            full_text_normalised=normalized,
            isnad_raw=None,
            isnad_normalised=None,
            matn_raw=arabic,
            matn_normalised=normalized,
            footnotes_json=None,
            source_url=f"{BASE_URL}{path}",
            extraction_method="thaqalayn_website_gap_fill_v1",
            extraction_confidence=100,
            review_status="website_verified_gap_fill",
        )
        db.add(hadith)
        db.flush()
        stats.created_hadiths += 1

        website_full = _plain_website_english(str(remote.get("english_text") or ""))
        if website_full:
            db.add(
                HadithTranslation(
                    hadith_id=hadith.id,
                    language="en",
                    translation_version=WEBSITE_TRANSLATION_VERSION,
                    source_full_sha256=sha256_text(hadith.full_text_raw),
                    source_isnad_sha256=None,
                    source_matn_sha256=sha256_text(hadith.matn_raw),
                    rendered_isnad_en=None,
                    matn_translation=website_full,
                    full_translation=website_full,
                    status="published",
                    risk_level="green",
                    risk_flags=[],
                    provider=WEBSITE_PROVIDER,
                    model="bab-ul-qaim-publications",
                    prompt_version=WEBSITE_QA_VERSION,
                    qa_version=WEBSITE_QA_VERSION,
                    input_tokens=0,
                    output_tokens=0,
                    cost_estimate_usd=0.0,
                    provenance_json={
                        "source": WEBSITE_PROVIDER,
                        "source_url": f"{BASE_URL}{path}",
                        "website_path": path,
                        "translator": corpus.translator,
                        "translation_classification": "external_source_normalized",
                        "source_english_sha256": sha256_text(website_full),
                        "source_website_arabic_sha256": str(
                            remote.get("arabic_sha256") or ""
                        ),
                        "source_inventory_sha256": inventory_sha256,
                        "match_method": "reviewed_numbered_gap_fill",
                        "matcher_version": WEBSITE_QA_VERSION,
                    },
                )
            )
            stats.created_translations += 1
    db.flush()
    return stats


def import_website_structure(
    db: Session,
    *,
    inventory: dict[str, Any],
    audit: dict[str, Any],
    dry_run: bool = True,
) -> WebsiteStructureImportStats:
    """Build transparent kitab/chapter placement from website-confirmed links."""

    corpus = _corpus_from_inventory(inventory)
    inventory_sha256 = _website_inventory_sha256(inventory)
    if audit.get("inventory_sha256") != inventory_sha256:
        raise ValueError("Website audit does not belong to the supplied inventory")

    book = db.execute(
        select(Book).where(Book.source_book_id == corpus.source_book_id)
    ).scalar_one()
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
    by_id = {hadith.id: hadith for hadith in hadiths}
    remote_by_path = {
        str(row["path"]): row for row in _inventory_rows(inventory)
    }
    rows_by_hadith: dict[int, dict[str, Any]] = {}
    stats = WebsiteStructureImportStats()

    for edge in audit.get("confirmed_relations", []):
        stats.confirmed += 1
        if edge.get("relation") != "one_to_one":
            continue
        hadith = by_id.get(int(edge["local_id"]))
        remote = remote_by_path.get(str(edge["website_path"]))
        if hadith is None or remote is None:
            continue
        rows_by_hadith[hadith.id] = {
            "remote_book_id": (
                f"{remote['remote_book_id']}:{remote['kitab_id']}:{remote['chapter_id']}"
            ),
            "remote_id": int(remote["number_in_chapter"]),
            "volume": int(remote["volume"]),
            "kitab_id": f"v{remote['volume']}-k{remote['kitab_id']}",
            "kitab_name_en": str(remote["kitab_name_en"]),
            "chapter_id": int(remote["chapter_id"]),
            "chapter_name_en": str(remote["chapter_name_en"]),
            "number_in_chapter": int(remote["number_in_chapter"]),
            "number_prefix_en": None,
            "position_computed": None,
            "numbering_flags": None,
            "thaqalayn_url": f"{BASE_URL}{remote['path']}",
            "mapping_status": "matched",
            "match_method": str(edge.get("method") or "website_arabic"),
            "match_score": float(edge.get("score") or 0.0),
            "remote_arabic_sha256": str(remote.get("arabic_sha256") or ""),
            "raw_ref_json": {
                "website_path": remote["path"],
                "chapter_path": remote["chapter_path"],
                "website_kitab_id": int(remote["kitab_id"]),
                "inventory_sha256": inventory_sha256,
            },
        }
        stats.matched += 1

    # Local edition fragments bounded by two confirmed rows in the same
    # website chapter inherit only that chapter placement. They do not claim a
    # remote report number or translation.
    matched_indexes = [
        index for index, hadith in enumerate(hadiths) if hadith.id in rows_by_hadith
    ]
    for left_index, right_index in zip(matched_indexes, matched_indexes[1:]):
        left = rows_by_hadith[hadiths[left_index].id]
        right = rows_by_hadith[hadiths[right_index].id]
        structure_key = ("volume", "kitab_id", "chapter_id")
        if any(left[key] != right[key] for key in structure_key):
            continue
        for hadith in hadiths[left_index + 1 : right_index]:
            if hadith.id in rows_by_hadith:
                continue
            rows_by_hadith[hadith.id] = {
                **left,
                "remote_book_id": None,
                "remote_id": None,
                "number_in_chapter": None,
                "thaqalayn_url": None,
                "mapping_status": "interpolated_unmapped",
                "match_method": "bounded_same_chapter",
                "match_score": None,
                "remote_arabic_sha256": None,
                "raw_ref_json": {
                    "left_anchor": hadiths[left_index].public_id,
                    "right_anchor": hadiths[right_index].public_id,
                    "inventory_sha256": inventory_sha256,
                },
            }
            stats.interpolated += 1

    stats.unmapped = len(hadiths) - len(rows_by_hadith)
    stats.written = len(rows_by_hadith)
    if dry_run:
        return stats

    hadith_ids = [hadith.id for hadith in hadiths]
    db.query(ThaqalaynStructureMap).filter(
        ThaqalaynStructureMap.hadith_id.in_(hadith_ids),
        ThaqalaynStructureMap.source == WEBSITE_PROVIDER,
    ).delete(synchronize_session=False)
    for hadith_id, values in rows_by_hadith.items():
        db.add(
            ThaqalaynStructureMap(
                hadith_id=hadith_id,
                source=WEBSITE_PROVIDER,
                matcher_version=WEBSITE_QA_VERSION,
                **values,
            )
        )
    db.flush()
    return stats


def render_audit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    inventory = audit["website_inventory"]
    quality = audit.get("publication_quality", {}).get("summary", {})
    inventory_ready = "YES" if summary.get("inventory_ready", summary["claim_ready"]) else "NO"
    rijal_ready = "YES" if summary.get("rijal_ready", False) else "NO"
    publication_ready = "YES" if summary.get("publication_ready", False) else "NO"
    return "\n".join(
        [
            f"# {audit.get('title', 'Al-Kafi')} website completeness audit",
            "",
            f"Audited: `{audit['audited_at']}`",
            f"Website witness: `{audit['source']}`",
            f"Inventory SHA-256: `{audit['inventory_sha256']}`",
            "",
            "## Result",
            "",
            f"- Local visible report units: **{summary['local_visible']:,}**",
            f"- Thaqalayn website reports: **{summary['website_hadiths']:,}**",
            f"- Local reports confirmed against website Arabic: **{summary['confirmed_local']:,}**",
            f"- Website reports confirmed against local Arabic: **{summary['confirmed_website']:,}**",
            f"- Reviewed local-edition-only reports: **{summary['reviewed_local_only']:,}**",
            f"- Reviewed website non-independent units: **{summary['reviewed_website_nonindependent']:,}**",
            f"- Missing numbered website reports: **{summary['website_numbered_gaps']:,}**",
            f"- Unclassified local / website units: **{summary['unclassified_local']:,} / {summary['unclassified_website']:,}**",
            f"- Candidate split/merge review blocks: **{summary['candidate_split_merge_blocks']:,}**",
            f"- Inventory reconciliation ready: **{inventory_ready}**",
            f"- Arabic boundaries ready for rijal: **{rijal_ready}**",
            f"- Public release ready: **{publication_ready}**",
            "",
            "The two editions do not need equal row counts. This inventory gate requires",
            "zero missing numbered reports and zero unclassified units after reviewed",
            "split, merge, editorial, and edition-only decisions. It does not certify",
            "record boundaries or translation completeness for public release.",
            "",
            "## Publication quality",
            "",
            f"- Blocking local records: **{quality.get('blocking_records', 0):,}**",
            f"- Boundary blockers: **{quality.get('boundary_blocking_records', 0):,}**",
            f"- Translation blockers: **{quality.get('translation_blocking_records', 0):,}**",
            f"- Mapped records below 90% displayed-Arabic coverage: **{quality.get('mapped_records_below_90_percent', 0):,}**",
            f"- Mapped records below 50% displayed-Arabic coverage: **{quality.get('mapped_records_below_50_percent', 0):,}**",
            f"- Non-one-to-one local boundaries: **{quality.get('non_one_to_one_records', 0):,}**",
            f"- Reviewed local-edition-only records: **{quality.get('reviewed_local_only_records', 0):,}**",
            f"- Unreviewed local-edition-only records: **{quality.get('unreviewed_local_only_records', 0):,}**",
            f"- Approved splits missing a detectable source isnad: **{quality.get('approved_splits_missing_detectable_isnad', 0):,}**",
            f"- Records missing website English: **{quality.get('records_missing_website_english', 0):,}**",
            f"- Records missing a published website translation: **{quality.get('records_missing_published_website_translation', 0):,}**",
            "",
            "Rijal readiness requires stable reviewed Arabic report boundaries and no",
            "detectable source isnad lost from the active split. Public release remains",
            "fail-closed on translation gaps as well. Evidence is retained in JSON.",
            "",
            "## Website inventory",
            "",
            f"- Chapter pages: **{inventory['chapter_count']:,}**",
            f"- Hadith sitemap routes: **{inventory['sitemap_path_count']:,}**",
            f"- Rendered reports: **{summary['website_hadiths']:,}**",
            f"- Non-report placeholders: **{inventory['non_report_count']:,}**",
            f"- Website display anomalies: **{inventory['anomaly_count']:,}**",
            "",
            f"Every {audit.get('title', 'Al-Kafi')} route in the website sitemap was found in the rendered",
            "chapter inventory. Placeholder and anomaly details are retained in JSON.",
            "",
            "## Reconciliation",
            "",
            f"- Bounded candidate blocks: **{summary['candidate_split_merge_blocks']:,}**",
            f"- Candidate local units: **{summary['candidate_local_reports']:,}**",
            f"- Candidate website reports: **{summary['candidate_website_reports']:,}**",
            f"- Hash-locked local-only reports: **{summary['reviewed_local_only']:,}**",
            f"- Hash-locked website editorial/subdivision units: **{summary['reviewed_website_nonindependent']:,}**",
            f"- Unclassified local units: **{summary['unclassified_local']:,}**",
            f"- Unclassified website units: **{summary['unclassified_website']:,}**",
            "",
            "## Method",
            "",
            "Rendered Thaqalayn chapter pages are the source witness. Existing API-derived",
            "structure mappings and translation URLs are treated only as candidate links;",
            "each accepted relation is reverified against Arabic rendered on the website.",
            "No database row is changed by this audit.",
            "",
        ]
    )
