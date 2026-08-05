"""Deciding whether a quoted report and a local hadith are the same report.

Shared by every commentary source, because the problem is the same one whatever
edition quotes the text: the two printings write the same words differently, and
none of those differences say anything about identity.

  * a commentary spells honorifics out («عليه‌السلام») where al-Kafi prints «ع»;
  * it attaches the conjunction («وعدوه») where al-Kafi detaches it («وَ عَدُوُّهُ»);
  * the quote carries its printed report number, the hadith does not.

Comparing raw tokens charges a correct match for typesetting, so these artefacts
are removed from *both* sides before any score is computed. Thresholds live with
the callers; this module only measures.
"""

from __future__ import annotations

from collections import defaultdict
import re

from eshia_research.models import Hadith
from eshia_research.normalise import normalise_arabic_persian
from eshia_research.translation.thaqalayn_importer import match_norm

# Must cover the Persian block, not just ء-ي. `normalise_arabic_persian` maps
# Arabic yeh (ي U+064A) to Persian yeh (ی U+06CC) and Arabic kaf (ك U+0643) to
# Persian kaf (ک U+06A9), both of which sit *above* U+064A. A range ending at
# ي therefore cut every normalised word at its first yeh or kaf — «التوحيد»
# tokenised as «التوح», and «يحيى» and «عيسى» produced no token at all, quietly
# deleting two of the commonest names in an al-Kafi isnad from the comparison.
ARABIC_WORD_RE = re.compile(r"[ء-يٮ-ۓٰ]+")

_HONORIFIC_TOKENS = {
    normalise_arabic_persian(word)
    for word in ("عليه", "عليها", "عليهم", "السلام", "صلى", "وآله", "آله", "ع", "ص")
}
_DIGITS_ONLY_RE = re.compile(r"^[0-9٠-٩۰-۹]+$")


def comparable_tokens(text: str | None) -> list[str]:
    """Tokens of a report or hadith, stripped of edition-specific spelling."""
    tokens: list[str] = []
    for raw in ARABIC_WORD_RE.findall(normalise_arabic_persian(text or "")):
        if _DIGITS_ONLY_RE.match(raw):
            continue
        # Detach a leading conjunction so "وعدوه" and "و عدوه" agree. Applied to
        # both sides, so words genuinely beginning with waw still match.
        token = raw[1:] if raw.startswith("و") and len(raw) > 3 else raw
        if token in _HONORIFIC_TOKENS or len(token) < 2:
            continue
        tokens.append(token)
    return tokens


# Every candidate hadith is re-scored against many passages; tokenising its
# text once per index run turns a quadratic cost into a linear one.
_hadith_token_cache: dict[int, list[str]] = {}


def clear_hadith_token_cache() -> None:
    _hadith_token_cache.clear()


def hadith_tokens(hadith: Hadith) -> list[str]:
    cached = _hadith_token_cache.get(hadith.id)
    if cached is None:
        cached = comparable_tokens(hadith.full_text_raw)
        _hadith_token_cache[hadith.id] = cached
    return cached


def incipit_aligned(source: list[str], target: list[str], *, width: int = 6) -> bool:
    """Does the quote reproduce the hadith's opening words, in order?

    Commentators routinely quote only the head of a long report. An opening that
    matches word-for-word is positive identification, not a partial overlap.
    """
    if len(source) < width or len(target) < width:
        return False
    return source[:width] == target[:width]


def score_report_text(text: str | None, hadith: Hadith) -> float | None:
    """0.0-1.0 similarity of a quoted report to a hadith; None if unusable."""
    if not text:
        return None
    report_norm = match_norm(text)
    source_tokens = comparable_tokens(text)
    target_tokens = hadith_tokens(hadith)
    source_words = set(source_tokens)
    target_words = set(target_tokens)
    target_norm = match_norm(hadith.full_text_raw)
    if not report_norm or len(source_words) < 5 or not target_norm:
        return None
    if report_norm in target_norm or target_norm in report_norm:
        return 1.0
    overlap = len(source_words & target_words)
    source_coverage = overlap / len(source_words)
    target_coverage = overlap / len(target_words) if target_words else 0.0
    length_ratio = len(source_words) / len(target_words) if target_words else 0.0
    # A quote whose every word occurs in the hadith *and* whose opening
    # reproduces the hadith's opening verbatim identifies it, however early the
    # commentator stopped copying.
    if (
        source_coverage >= 0.97
        and len(source_tokens) >= 10
        and incipit_aligned(source_tokens, target_tokens)
    ):
        return 1.0
    # Editions expand compact honorifics. When every local report word is
    # independently present and the source adds only a little extra text, this
    # is the same report rather than a loose topical overlap. The extent gate
    # stays explicit so an attached commentary paragraph cannot pass as a report.
    if (
        target_coverage >= 0.98
        and source_coverage >= 0.84
        and 0.7 <= length_ratio <= 1.35
    ):
        return 1.0
    return round((0.7 * source_coverage) + (0.3 * target_coverage), 6)


def hadith_word_index(hadiths: list[Hadith]) -> dict[str, list[Hadith]]:
    index: dict[str, list[Hadith]] = defaultdict(list)
    for hadith in hadiths:
        for word in set(hadith_tokens(hadith)):
            index[word].append(hadith)
    return index


def best_text_candidate(
    text: str | None,
    word_index: dict[str, list[Hadith]],
    hadith_by_id: dict[int, Hadith],
) -> tuple[Hadith | None, float | None, float | None]:
    """Best-scoring hadith for a quoted report, plus the runner-up's score.

    Candidates are gathered from the report's *rarest* words, so a common
    formula like «عدة من أصحابنا» never drags in the whole corpus.
    """
    if not text:
        return None, None, None
    report_words = set(comparable_tokens(text))
    if len(report_words) < 8:
        return None, None, None
    rare_words = sorted(report_words, key=lambda word: (len(word_index.get(word, [])), -len(word)))
    candidate_ids: set[int] = set()
    for word in rare_words[:5]:
        candidate_ids.update(hadith.id for hadith in word_index.get(word, []))
    scored = [
        (score_report_text(text, hadith_by_id[hadith_id]), hadith_by_id[hadith_id])
        for hadith_id in candidate_ids
    ]
    scored = [(score, hadith) for score, hadith in scored if score is not None]
    if not scored:
        return None, None, None
    scored.sort(key=lambda item: item[0] or 0.0, reverse=True)
    best_score, best = scored[0]
    runner_up = scored[1][0] if len(scored) > 1 else None
    return best, best_score, runner_up
