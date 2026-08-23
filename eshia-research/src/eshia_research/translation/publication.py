"""Fail-closed policy for translations exposed by the public product.

Keep every public read path on this module.  The SQL filters cheaply discard
obvious non-public rows; :func:`is_public_english_translation` is the final
authority because source-currentness requires hashing the active hadith text.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

from sqlalchemy import String, and_, cast, func, or_

from eshia_research.models import Hadith, HadithTranslation
from eshia_research.normalise import strip_diacritics
from eshia_research.translation import TRANSLATION_VERSION
from eshia_research.translation.text import FOOTNOTE_MARKER_RE, sha256_text, source_norm


# Clearly-labelled AI translation tier. These rows are NOT human editions and
# never claim to be; they exist only to fill gaps where no human translation
# exists, and the UI must tag them "AI translation — verify against the Arabic".
# They still pass every non-provenance safety check (status, green risk level,
# no critical flag, and — crucially — the source-hash currency test, so a row
# auto-hides the moment its Arabic changes). Ranked LAST below, so a human
# edition always wins when both exist.
AI_TRANSLATION_VERSIONS = ("ai_sarwar_v1",)

# Translation versions that may publish, in descending preference order. When a
# hadith has more than one publishable row, the earliest version in this tuple
# wins. Rendered website text is authoritative; API and legacy imports remain
# available as fallbacks and immutable source history; the AI tier fills only
# what no human edition covers.
PUBLIC_TRANSLATION_VERSIONS = (
    "thaqalayn_website_v1",
    "thaqalayn_live_v1",
    TRANSLATION_VERSION,
    *AI_TRANSLATION_VERSIONS,
)

PUBLIC_TRANSLATION_STATUSES = ("human_reviewed", "published")

# Public English must carry positive evidence that it came from a human
# edition, not merely avoid an AI-looking provider name.  Keep this vocabulary
# deliberately narrow; a new editorial workflow must declare and test its
# publication classification before its output can reach readers.
PUBLIC_TRANSLATION_CLASSIFICATIONS = (
    "external_source_normalized",
    "verbatim_external_matn_excerpt",
    "bounded_external_excerpt",
)

# These markers deliberately err on the side of hiding a row.  A public
# translation must be attributable to an external human source or human
# review; ambiguous machine-generated provenance is not publishable.
FORBIDDEN_AI_MARKERS = (
    "codex",
    "openai",
    "gpt",
    "llm",
    "ai-generated",
    "ai_generated",
    "ai generated",
    "machine-generated",
    "machine_generated",
    "machine generated",
    "artificial intelligence",
    "project_authored",
    "project-authored",
    "project authored",
)


def _provenance_text(provenance: object) -> str:
    if provenance is None:
        return ""
    if isinstance(provenance, str):
        return provenance
    try:
        return json.dumps(provenance, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(provenance)


def has_forbidden_ai_marker(*values: object) -> bool:
    """Return true when any provider/model/provenance value signals AI text."""

    haystack = " ".join(_provenance_text(value) for value in values).casefold()
    return any(marker in haystack for marker in FORBIDDEN_AI_MARKERS)


def has_public_human_source_metadata(provenance: object) -> bool:
    """Require an attributed translator and an approved external-source class."""

    if not isinstance(provenance, dict):
        return False
    translator = provenance.get("translator")
    classification = provenance.get("translation_classification") or provenance.get(
        "classification"
    )
    return bool(
        isinstance(translator, str)
        and translator.strip()
        and isinstance(classification, str)
        and classification in PUBLIC_TRANSLATION_CLASSIFICATIONS
    )


def has_blocking_risk_flag(flags: object) -> bool:
    """Fail closed when a row is labelled green but retains a critical flag."""

    return bool(
        isinstance(flags, list)
        and any(
            isinstance(flag, dict) and flag.get("severity") == "critical"
            for flag in flags
        )
    )


def public_english_translation_candidate_filters() -> Sequence[object]:
    """SQL predicates shared by every public English-translation query.

    Hash validation is intentionally not represented here: supported SQL
    backends do not all provide the same SHA-256 function.  Callers must pass
    every candidate through :func:`is_public_english_translation`.
    """

    provenance_text = func.lower(func.coalesce(cast(HadithTranslation.provenance_json, String), ""))
    provider_text = func.lower(func.coalesce(HadithTranslation.provider, ""))
    model_text = func.lower(func.coalesce(HadithTranslation.model, ""))
    is_ai_version = HadithTranslation.translation_version.in_(AI_TRANSLATION_VERSIONS)
    filters: list[object] = [
        HadithTranslation.language == "en",
        HadithTranslation.translation_version.in_(PUBLIC_TRANSLATION_VERSIONS),
        HadithTranslation.status.in_(PUBLIC_TRANSLATION_STATUSES),
        HadithTranslation.risk_level == "green",
        HadithTranslation.matn_translation.isnot(None),
        func.length(func.trim(HadithTranslation.matn_translation)) > 0,
    ]
    # AI-marker exclusion applies to the HUMAN tier only — the AI tier is
    # expected to carry those markers and is gated by its own explicit branch in
    # is_public_english_translation().
    for marker in FORBIDDEN_AI_MARKERS:
        pattern = f"%{marker}%"
        filters.append(
            or_(
                is_ai_version,
                and_(
                    ~provider_text.like(pattern),
                    ~model_text.like(pattern),
                    ~provenance_text.like(pattern),
                ),
            )
        )
    return tuple(filters)


def source_hashes_are_current(translation: HadithTranslation, hadith: Hadith) -> bool:
    """Check all three source hashes against the active Arabic fields."""

    return source_hash_values_are_current(
        source_full_sha256=translation.source_full_sha256,
        source_isnad_sha256=translation.source_isnad_sha256,
        source_matn_sha256=translation.source_matn_sha256,
        full_text_raw=hadith.full_text_raw,
        isnad_raw=hadith.isnad_raw,
        matn_raw=hadith.matn_raw,
    )


def source_hash_values_are_current(
    *,
    source_full_sha256: str,
    source_isnad_sha256: str | None,
    source_matn_sha256: str,
    full_text_raw: str,
    isnad_raw: str | None,
    matn_raw: str,
) -> bool:
    """Column-oriented hash check for bulk metrics without ORM hydration."""

    expected_isnad_sha256 = sha256_text(isnad_raw) if isnad_raw else None
    return bool(
        source_full_sha256 == sha256_text(full_text_raw)
        and source_isnad_sha256 == expected_isnad_sha256
        and source_matn_sha256 == sha256_text(matn_raw)
    )


# Which Arabic a stored English text still provably corresponds to.
TRANSLATION_SCOPE_SPLIT = "split"
TRANSLATION_SCOPE_REPORT = "report"

_ZERO_WIDTH_RE = re.compile(r"[​-‏‪-‮⁦-⁩]")
_NON_WORD_RE = re.compile(r"[^\w]+", re.UNICODE)


def _comparison_key(text: str | None) -> str:
    """Reduce Arabic to what a containment check can honestly compare.

    Splitting a report drops the separators the edition prints between chain
    and body — a dash, a zero-width joiner glued to the honorific («ع‌-») —
    and the two sides carry different footnote markers and case endings for
    the same word. None of that is a difference in *text*, so it is removed
    before comparing; what remains is letters.
    """
    stripped = FOOTNOTE_MARKER_RE.sub(" ", text or "")
    stripped = _ZERO_WIDTH_RE.sub("", strip_diacritics(stripped))
    return _NON_WORD_RE.sub("", source_norm(stripped))


def report_contains_its_parts(hadith: Hadith) -> bool:
    """Are the isnad and matn still drawn from the report they belong to?

    This is what separates a re-split from a corruption. Both move the split
    hashes; only one leaves parts that are still the report's own words. A
    matn that is no longer found in `full_text_raw` is not a boundary that
    moved, it is a body that was replaced, and no translation of the report
    may be shown beside it.
    """
    report = _comparison_key(hadith.full_text_raw)
    if not report:
        return False
    matn = _comparison_key(hadith.matn_raw)
    if not matn or matn not in report:
        return False
    isnad = _comparison_key(hadith.isnad_raw)
    return not isnad or isnad in report


def translation_source_scope(
    translation: HadithTranslation, hadith: Hadith
) -> str | None:
    """What the stored English can still be shown against, or None.

    The three hashes answer two different questions, and collapsing them into
    one boolean threw away the useful half.

    ``source_full_sha256`` guards the *report*: if it no longer matches, the
    Arabic itself has changed underneath the translation and nothing may be
    shown. That check is unchanged and still fails closed.

    The isnad and matn hashes guard our own *editorial boundary*, which is not
    a property of the text. Re-splitting a report — moving «وَ قَالَ الصَّادِقُ ع»
    out of the body and into the chain — changes both without altering a
    character of what was translated. Withholding the English then hides a
    correct translation because we revised our own parse, and the translation
    is usually of the whole report anyway: Bab ul Qaim's Faqih text opens
    "Imam Jafar ibn Muhammad Al-Sadiq (as) said:", which is the isnad.

    So a report whose text is intact but whose split has moved is publishable
    at report scope, and the caller is told which it got so the interface can
    say what the English covers rather than implying it renders the matn alone.
    """
    if translation.source_full_sha256 != sha256_text(hadith.full_text_raw):
        return None
    expected_isnad_sha256 = sha256_text(hadith.isnad_raw) if hadith.isnad_raw else None
    if (
        translation.source_isnad_sha256 == expected_isnad_sha256
        and translation.source_matn_sha256 == sha256_text(hadith.matn_raw)
    ):
        return TRANSLATION_SCOPE_SPLIT
    if not report_contains_its_parts(hadith):
        return None
    return TRANSLATION_SCOPE_REPORT


def is_public_english_translation(
    translation: HadithTranslation | None,
    hadith: Hadith,
) -> bool:
    """Final, fail-closed decision for public English translation exposure."""

    if translation is None:
        return False
    if translation.language != "en" or translation.translation_version not in PUBLIC_TRANSLATION_VERSIONS:
        return False
    if translation.status not in PUBLIC_TRANSLATION_STATUSES:
        return False
    if translation.risk_level != "green" or not (translation.matn_translation or "").strip():
        return False
    if has_blocking_risk_flag(translation.risk_flags):
        return False
    if translation.translation_version in AI_TRANSLATION_VERSIONS:
        # Clearly-labelled AI tier: no human-source requirement (it isn't human,
        # and the UI tags it as such), but still hash-guarded so stale text hides.
        return translation_source_scope(translation, hadith) is not None
    if has_forbidden_ai_marker(
        translation.provider,
        translation.model,
        translation.provenance_json,
    ):
        return False
    if not has_public_human_source_metadata(translation.provenance_json):
        return False
    return translation_source_scope(translation, hadith) is not None
