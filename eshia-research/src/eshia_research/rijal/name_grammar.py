"""Formal grammar for Arabic narrator names (the nasab calculus).

A narrator name is compositional: ``ism (بن ism)* [kunya] [nisba/laqab...]``.
This module parses a name into structured parts and deterministically
generates every surface form the person can legally appear under in an isnad
(nasab truncations, kunya, ibn-form, nisba-form).

Two facts drive the design:

* the nasab itself asserts kinship — for «فلان بن X» the father IS named X,
  so father names come for free from parsing;
* a bare form like «أحمد بن محمد» is a truncation shared by many persons, so
  ambiguity is made explicit by construction (see PersonSurfaceForm.shared_count)
  instead of being an accident of string matching.

All parsing operates on `normalise_arabic_persian` output (Persian ی/ک), the
same normalisation used for `chain_nodes.token_normalised` — forms produced
here are directly joinable against chain mentions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eshia_research.normalise import normalise_arabic_persian


def _n(text: str) -> str:
    return normalise_arabic_persian(text)


# Words that join two name units inside a nasab.
_BIN_WORDS = {_n("بن"), _n("ابن")}
# Kunya markers in all three case forms (nominative/genitive/accusative).
_KUNYA_WORDS = {_n("ابو"), _n("ابی"), _n("ابا"), _n("ام")}
_KUNYA_CANONICAL = _n("ابو")
_KUNYA_VARIANTS = (_n("ابو"), _n("ابی"), _n("ابا"))
# First half of theophoric compounds: عبد الله, عبد الرحمن, عبيد الله ...
_COMPOUND_HEADS = {_n("عبد"), _n("عبید")}
# Honorific prefixes that are not part of the name proper.
_TITLE_PREFIXES = {_n("الشیخ"), _n("السید"), _n("المولی"), _n("الملا"), _n("میرزا")}
_IBN_WORD = _n("ابن")
_BIN_JOIN = f" {_n('بن')} "


@dataclass(frozen=True)
class ParsedName:
    """Structured decomposition of one narrator name (normalised)."""

    norm: str
    # Nasab chain: units[0] is the person's own ism, units[1] their father,
    # units[2] the grandfather, ... Each unit may itself be a compound
    # («عبد الله») or a kunya («ابی عمیر» in محمد بن ابی عمیر).
    units: tuple[str, ...] = ()
    kunya: str | None = None
    # Trailing definite-article tokens: nisbas and laqabs («الاشعری القمی»).
    nisba_parts: tuple[str, ...] = ()
    # True for ibn-form names like «ابن محبوب»: units then hold the ancestor
    # name(s), not the person's own ism.
    is_ibn_form: bool = False
    # Tokens the grammar could not classify; kept for honesty, never guessed.
    residue: tuple[str, ...] = ()

    @property
    def father_norm(self) -> str | None:
        """The father's name chain asserted by the nasab itself."""
        if self.is_ibn_form:
            return _BIN_JOIN.join(self.units) if self.units else None
        if len(self.units) >= 2:
            return _BIN_JOIN.join(self.units[1:])
        return None


@dataclass(frozen=True)
class SurfaceForm:
    form_norm: str
    derivation: str


def _read_unit(tokens: list[str], i: int) -> tuple[str, int]:
    """Consume one name unit starting at tokens[i].

    Handles compounds (عبد الله) and kunya-shaped units (ابی عمیر,
    ابی عبد الله) which occur both as isms and as fathers.
    """
    token = tokens[i]
    if token in _COMPOUND_HEADS and i + 1 < len(tokens):
        return f"{token} {tokens[i + 1]}", i + 2
    if token in _KUNYA_WORDS and i + 1 < len(tokens):
        inner, j = _read_unit(tokens, i + 1)
        return f"{token} {inner}", j
    return token, i + 1


def parse_name(raw: str) -> ParsedName:
    norm = _n(raw)
    tokens = norm.split()
    if not tokens:
        return ParsedName(norm=norm)

    residue: list[str] = []
    while tokens and tokens[0] in _TITLE_PREFIXES:
        residue.append(tokens.pop(0))

    if not tokens:
        return ParsedName(norm=norm, residue=tuple(residue))

    units: list[str] = []
    kunya: str | None = None
    is_ibn_form = False
    i = 0

    def _is_nisba(token: str) -> bool:
        return token.startswith(_n("ال")) and len(token) > 3

    if tokens[0] == _IBN_WORD and len(tokens) > 1:
        # «ابن محبوب»: the name gives only the ancestor.
        is_ibn_form = True
        i = 1
        unit, i = _read_unit(tokens, i)
        units.append(unit)
    else:
        # Optional leading kunya («ابو جعفر محمد بن یعقوب», «ابو بصیر»).
        if tokens[0] in _KUNYA_WORDS:
            unit, i = _read_unit(tokens, 0)
            kunya = unit
        # The ism. Many isms begin with ال (الحسن، العلاء، الفضل), so a
        # leading ال-word is still the ism unless we already have a kunya and
        # it is a trailing nisba (not heading a nasab) — «ابو ابراهیم الازدی».
        if i < len(tokens) and tokens[i] not in _BIN_WORDS:
            next_is_bin = i + 1 < len(tokens) and tokens[i + 1] in _BIN_WORDS
            trailing_nisba = kunya is not None and _is_nisba(tokens[i]) and not next_is_bin
            if not trailing_nisba:
                unit, i = _read_unit(tokens, i)
                units.append(unit)

    # Continue the nasab: (بن unit)*
    while i < len(tokens) and tokens[i] in _BIN_WORDS:
        if i + 1 >= len(tokens):
            residue.append(tokens[i])
            i += 1
            break
        unit, j = _read_unit(tokens, i + 1)
        units.append(unit)
        i = j

    # After the chain: an optional kunya, then nisba/laqab tokens.
    while i < len(tokens):
        token = tokens[i]
        if kunya is None and token in _KUNYA_WORDS and i + 1 < len(tokens):
            unit, i = _read_unit(tokens, i)
            kunya = unit
            continue
        break

    nisba_parts: list[str] = []
    for token in tokens[i:]:
        if token.startswith(_n("ال")) and len(token) > 3:
            nisba_parts.append(token)
        else:
            residue.append(token)

    if kunya is not None:
        # Canonicalise the case form: ابی/ابا -> ابو at the head of the kunya.
        head, _, rest = kunya.partition(" ")
        if head in _KUNYA_WORDS and rest:
            kunya = f"{_KUNYA_CANONICAL} {rest}" if head != _n("ام") else kunya

    return ParsedName(
        norm=norm,
        units=tuple(units),
        kunya=kunya,
        nisba_parts=tuple(nisba_parts),
        is_ibn_form=is_ibn_form,
        residue=tuple(residue),
    )


def _kunya_case_variants(form: str) -> list[str]:
    """«ابو فلان» is genitive «ابی فلان» after عن — generate all case forms."""
    head, _, rest = form.partition(" ")
    if head not in _KUNYA_VARIANTS or not rest:
        return [form]
    return [f"{variant} {rest}" for variant in _KUNYA_VARIANTS]


def surface_forms(parsed: ParsedName, max_forms: int = 16) -> list[SurfaceForm]:
    """Every legal isnad appearance of this person, most specific first.

    Single-ism and nisba-only forms are deliberately included even though they
    are extremely ambiguous — shared_count carries that signal; suppressing
    the forms would hide it.
    """
    out: list[SurfaceForm] = []
    seen: set[str] = set()

    def add(form: str, derivation: str) -> None:
        form = form.strip()
        if form and form not in seen and len(out) < max_forms:
            seen.add(form)
            out.append(SurfaceForm(form_norm=form, derivation=derivation))

    nisba0 = parsed.nisba_parts[0] if parsed.nisba_parts else None

    if parsed.is_ibn_form:
        if parsed.units:
            add(f"{_IBN_WORD} {parsed.units[0]}", "full")
        return out

    units = parsed.units
    if units:
        full = _BIN_JOIN.join(units)
        add(full, "full")
        if nisba0:
            add(f"{full} {nisba0}", "full")
        # Right-truncations of the nasab: احمد بن محمد بن عیسی ->
        # «احمد بن محمد», «احمد».
        for k in range(len(units) - 1, 0, -1):
            trunc = _BIN_JOIN.join(units[:k])
            add(trunc, "nasab_truncation" if k > 1 else "first_name")
            if nisba0:
                add(f"{trunc} {nisba0}", "nasab_truncation" if k > 1 else "first_name")
        # Ibn-forms: by the father and by the most distant (often most famous)
        # ancestor: الحسن بن محبوب -> «ابن محبوب».
        if len(units) >= 2:
            add(f"{_IBN_WORD} {units[1]}", "ibn_form")
            if len(units) >= 3:
                add(f"{_IBN_WORD} {units[-1]}", "ibn_form")

    if parsed.kunya:
        for variant in _kunya_case_variants(parsed.kunya):
            add(variant, "kunya")
        if nisba0:
            for variant in _kunya_case_variants(parsed.kunya):
                add(f"{variant} {nisba0}", "kunya")

    if nisba0 and units:
        add(nisba0, "nisba_form")

    return out
