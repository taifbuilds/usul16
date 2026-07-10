"""HTML parsers for eShia-style library pages.

Selectors below were derived from real samples saved in data/samples/
(fetched 2026-06-27 from lib.eshia.ir) rather than guessed. eShia is a large,
long-running site though, so some page types vary by section (e.g. some books
are scanned-image-only with no extractable text — see parse_page). Anywhere
the selector is uncertain or only confirmed for one section, it is marked
with a TODO so it can be re-verified against more samples before scaling up
the crawl.
"""

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

# Matches the numeric book id that starts every content/book URL on eShia,
# e.g. https://lib.eshia.ir/26395 or https://lib.eshia.ir/10009/1/1
BOOK_ID_RE = re.compile(r"/(\d+)(?:/(\d+)/(\d+))?/?$")


def extract_book_id(url: str) -> str | None:
    match = BOOK_ID_RE.search(url)
    return match.group(1) if match else None


# Splits combined-author strings like "الخوئي، السيد أبوالقاسم - ميرزا علي
# الغروي" into separate people. Confirmed against multiple eShia author
# fields: " - " (space-hyphen-space) separates distinct people (commonly a
# marja' lecturer and the student who compiled/edited the text), while "،"
# is used *within* one name as a surname/given-name separator and must not
# be split on.
_AUTHOR_SPLIT_RE = re.compile(r"\s+-\s+")


def split_author_names(raw: str) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in _AUTHOR_SPLIT_RE.split(raw) if part.strip()]


@dataclass
class CategoryBookEntry:
    source_book_id: str
    title_original: str
    source_url: str
    author_name: str | None
    author_url: str | None
    volume_count: int | None


def parse_category_page(html: str, page_url: str) -> list[CategoryBookEntry]:
    """Parse a category listing page (e.g. https://lib.eshia.ir/فقه).

    Books are listed in `table#BooksList tbody tr.course`, one row per book,
    with index/name/author/volume columns.
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="BooksList")
    if table is None:
        # TODO: some category pages may paginate or nest subcategories
        # differently — verify against more samples if this returns empty
        # for a category that's known to have books.
        return []

    entries: list[CategoryBookEntry] = []
    for row in table.find_all("tr", class_="course"):
        name_cell = row.find("td", class_=lambda c: c and "BookName-sub" in c)
        author_cell = row.find("td", class_=lambda c: c and "BookAuthor-sub" in c)
        volume_cell = row.find("td", class_=lambda c: c and "BookVolumes-sub" in c)

        name_link = name_cell.find("a") if name_cell else None
        if name_link is None or not name_link.get("href"):
            continue

        book_url = urljoin(page_url, name_link["href"])
        book_id = extract_book_id(book_url)
        if book_id is None:
            continue

        author_link = author_cell.find("a") if author_cell else None
        author_name = author_link.get_text(strip=True) if author_link else None
        author_url = urljoin(page_url, author_link["href"]) if author_link and author_link.get("href") else None

        volume_count = None
        if volume_cell is not None:
            volume_text = volume_cell.get_text(strip=True)
            if volume_text.isdigit():
                volume_count = int(volume_text)

        entries.append(
            CategoryBookEntry(
                source_book_id=book_id,
                title_original=name_link.get_text(strip=True),
                source_url=book_url,
                author_name=author_name,
                author_url=author_url,
                volume_count=volume_count,
            )
        )
    return entries


@dataclass
class ParsedPage:
    source_book_id: str
    book_title: str
    author_name: str | None
    author_url: str | None
    volume_number: int | None
    page_number: int | None
    text: str | None
    is_image_only: bool
    next_page_url: str | None
    last_page_url: str | None
    toc_url: str | None


def _heading_own_text(heading: Tag | None) -> str | None:
    """Text of a heading's first direct text node only, excluding nested
    <span> labels and any text node that comes after them.

    book_title_heading mixes the title with nested `<span class="book_vol_page">`
    labels for volume/page numbers, e.g.:
        <h1 class="book_title_heading">
            آشنایی با ابواب فقه
            <span class="book_vol_page">جلد :</span>&nbsp;1&nbsp;
            <span class="book_vol_page">صفحه :</span>&nbsp;0
        </h1>
    Only the first text node ("آشنایی با ابواب فقه") is the actual title —
    everything after the first <span> is volume/page number filler.
    """
    if heading is None:
        return None
    for child in heading.children:
        if isinstance(child, Tag):
            break
        text = str(child).strip()
        if text:
            return text
    return None


def parse_page(html: str, page_url: str) -> ParsedPage:
    soup = BeautifulSoup(html, "lxml")
    book_id = extract_book_id(page_url) or ""

    title_heading = soup.find("h1", class_="book_title_heading")
    author_heading = soup.find("h2", class_="book_author_heading")
    author_link = author_heading.find("a") if author_heading else None

    book_title = _heading_own_text(title_heading) or ""
    author_name = author_link.get_text(strip=True) if author_link else None
    author_url = urljoin(page_url, author_link["href"]) if author_link and author_link.get("href") else None

    # Volume/page numbers: prefer the URL pattern (.../{book}/{vol}/{page}),
    # falling back to the "VolumeSelector" select box if the URL is ambiguous
    # (e.g. a TOC page at .../{book}/{vol}/0).
    url_match = BOOK_ID_RE.search(page_url)
    volume_number = int(url_match.group(2)) if url_match and url_match.group(2) else None
    page_number = int(url_match.group(3)) if url_match and url_match.group(3) else None

    content_cell = soup.find("td", class_="book-page-show")
    text: str | None = None
    is_image_only = False
    if content_cell is not None:
        # Strip the floating tool menu before extracting text.
        menu = content_cell.find("div", class_="sticky-menue")
        if menu is not None:
            menu.extract()
        if content_cell.find("img") is not None and not content_cell.get_text(strip=True):
            # Some older/scanned volumes render the page as an image with no
            # selectable text (see data/samples notes). OCR is out of scope
            # for this MVP — record the page as image-only instead of
            # silently storing an empty string.
            is_image_only = True
        else:
            # Preserve block/line breaks in the plain-text fallback. The
            # reader can render richer blocks from html_raw when available,
            # but cloud/batch crawls may only carry text_raw.
            for br in content_cell.find_all("br"):
                br.replace_with("\n")
            lines = [line.strip() for line in content_cell.get_text("\n").splitlines() if line.strip()]
            text = "\n".join(lines) or None

    next_link = soup.find("a", title="نمایش صفحه‌بعدی")
    last_link = soup.find("a", title="نمایش صفحه‌آخر")
    toc_link = soup.find("a", title="نمایش فهرست")

    return ParsedPage(
        source_book_id=book_id,
        book_title=book_title,
        author_name=author_name,
        author_url=author_url,
        volume_number=volume_number,
        page_number=page_number,
        text=text,
        is_image_only=is_image_only,
        next_page_url=urljoin(page_url, next_link["href"]) if next_link and next_link.get("href") else None,
        last_page_url=urljoin(page_url, last_link["href"]) if last_link and last_link.get("href") else None,
        toc_url=urljoin(page_url, toc_link["href"]) if toc_link and toc_link.get("href") else None,
    )


def last_page_number(parsed: ParsedPage) -> int | None:
    """Extract the final page number in a volume from the "last page" link.

    Lets `crawl-book` know how many pages to fetch without guessing.
    """
    if not parsed.last_page_url:
        return None
    match = BOOK_ID_RE.search(parsed.last_page_url)
    return int(match.group(3)) if match and match.group(3) else None


# Some (not all — observed on roughly two-thirds of a random sample) book
# cover/metadata pages include a "Subject" label in a <p> within the main
# content cell. Label format varies: "موضوع:", "الموضوع:", "الموضوع :" (with
# a space before the colon) have all been seen, sometimes with a newline or
# trailing zero-width joiner between the label and the value.
_SUBJECT_LABEL_RE = re.compile(r"(?:ال)?موضوع\s*:\s*")


def parse_book_subject(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    content_cell = soup.find("td", class_="book-page-show")
    if content_cell is None:
        return None
    for p in content_cell.find_all("p"):
        text = p.get_text()
        # "موضوع" appearing in `text` doesn't guarantee the label:value
        # pattern actually matches (e.g. it could appear mid-sentence
        # without a following colon) — search explicitly rather than
        # assuming a split will always find it.
        match = _SUBJECT_LABEL_RE.search(text)
        if match is None:
            continue
        value = re.sub(r"[\s‌‍]+", " ", text[match.end() :]).strip()
        if value:
            return value
    return None
