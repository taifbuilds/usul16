"""Deterministic QA checks for draft hadith translations."""

from __future__ import annotations

from dataclasses import dataclass, field

from eshia_research.translation import QA_VERSION
from eshia_research.translation.text import (
    arabic_char_count,
    arabic_ratio,
    clean_ws,
    footnote_markers,
    number_tokens,
)


@dataclass(frozen=True)
class GlossaryRequirement:
    source_term: str
    target_term: str


@dataclass(frozen=True)
class QAFlag:
    code: str
    severity: str
    detail: str


@dataclass
class QAReport:
    qa_version: str = QA_VERSION
    risk_level: str = "green"
    flags: list[QAFlag] = field(default_factory=list)

    @property
    def flag_codes(self) -> list[str]:
        return [flag.code for flag in self.flags]

    def add(self, code: str, severity: str, detail: str) -> None:
        self.flags.append(QAFlag(code=code, severity=severity, detail=detail))

    def finalize(self) -> "QAReport":
        severities = {flag.severity for flag in self.flags}
        if "critical" in severities:
            self.risk_level = "red"
        elif self.flags:
            self.risk_level = "amber"
        else:
            self.risk_level = "green"
        return self


def assess_translation(
    source_text: str,
    translation_text: str | None,
    *,
    glossary_requirements: list[GlossaryRequirement] | None = None,
    required_placeholders: set[str] | None = None,
) -> QAReport:
    """Run cheap, deterministic checks before any translation is trusted.

    These checks do not judge literary quality. They catch the mistakes that
    should never reach a reviewer: missing output, corrupted numbers, dropped
    placeholders, untranslated Arabic blocks, and obvious length collapses.
    """

    source = clean_ws(source_text)
    translation = clean_ws(translation_text)
    report = QAReport()

    if not translation:
        report.add("empty_translation", "critical", "Translation text is empty.")
        return report.finalize()

    source_numbers = number_tokens(source)
    translation_numbers = number_tokens(translation)
    if sorted(source_numbers) != sorted(translation_numbers):
        report.add(
            "number_mismatch",
            "critical",
            f"Source numbers {source_numbers} do not match translation numbers {translation_numbers}.",
        )

    source_markers = footnote_markers(source)
    translation_markers = footnote_markers(translation)
    required = set(required_placeholders or set()) | source_markers
    missing_markers = sorted(required - translation_markers)
    if missing_markers:
        report.add(
            "missing_placeholder",
            "critical",
            f"Missing marker(s) in translation: {', '.join(missing_markers)}.",
        )

    source_words = len(source.split())
    translation_words = len(translation.split())
    if source_words >= 12 and translation_words < max(4, int(source_words * 0.22)):
        report.add(
            "translation_too_short",
            "warning",
            f"Translation has {translation_words} words for {source_words} source words.",
        )
    if source_words >= 12 and translation_words > source_words * 5 + 60:
        report.add(
            "translation_too_long",
            "warning",
            f"Translation has {translation_words} words for {source_words} source words.",
        )

    if arabic_char_count(translation) >= 20 and arabic_ratio(translation) > 0.25:
        report.add(
            "untranslated_arabic_block",
            "warning",
            "Translation still contains a large Arabic-script block.",
        )

    lowered = translation.lower()
    for bad in ("i cannot translate", "as an ai", "cannot provide"):
        if bad in lowered:
            report.add("provider_refusal_text", "critical", f"Provider text found: {bad}.")

    for requirement in glossary_requirements or []:
        if requirement.source_term in source and requirement.target_term.lower() not in lowered:
            report.add(
                "glossary_miss",
                "warning",
                f"Expected '{requirement.target_term}' for source term '{requirement.source_term}'.",
            )

    return report.finalize()

