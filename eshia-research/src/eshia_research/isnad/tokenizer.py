"""Stage-1 isnad tokenizer: split a raw isnad into classified person-tokens.

This stage does **no identity resolution** — «أبيه» stays «أبيه» and
«أحمد بن محمد» is not guessed. It only answers: how many chains does this
isnad contain, what person-like tokens appear in each, in what order, and
what *kind* of token each is (named narrator, relational pronoun,
collective phrase, unknown person, Imam)?

Design choices grounded in the real Four-Books text:

- All matching happens on `normalise_arabic_persian`-normalised text so that
  alif/yeh/kaf variants can never desync a pattern from the data. The
  original isnad is preserved untouched on the Chain row.
- Same-tier co-narrators («عن حماد عن عمر بن أذينة وحريز عن زرارة») are
  expanded into parallel chains — the semantics are unambiguous.
- «جميعا» convergences and «وعن»-forks are NOT expanded: where the second
  route re-attaches is genuinely ambiguous without narrator knowledge, so
  the chain is kept linear and flagged ``multi_route`` for the resolution
  stage instead of baking in a guess.
- A chain stops at the first Imam token. Everything after it is the
  question topic or matn spill («سأل ... أبا عبد الله ع عن السطح...») and
  is deliberately discarded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from eshia_research.normalise import normalise_arabic_persian, strip_diacritics

# Real Al-Kafi co-narrator lists reach 24 unambiguous combinations (for
# example several named reporters transmitting from either of two Imams).
# Keeping the old cap of 8 silently retained only the first route. 32 covers
# every canonical Al-Kafi case while still bounding combinatorial expansion.
MAX_EXPANDED_CHAINS = 32

# --- token/node types -------------------------------------------------------
NAMED = "named_narrator"
PRONOUN = "pronoun_relation"
COLLECTIVE = "collective_phrase"
UNKNOWN = "unknown_person"
IMAM = "imam"

REVIEW_FLAGS = {
    "multi_route",
    "citation_noise",
    "matn_spill",
    "no_parseable_chain",
    "co_narrator_cap",
    "suspicious_token",
}


def _n(text: str) -> str:
    """Normalise a pattern literal the same way the working text is."""
    return normalise_arabic_persian(text)


@dataclass
class IsnadToken:
    raw: str
    norm: str
    phrase: str | None  # transmission phrase that introduced this token
    node_type: str
    relation_kind: str | None = None


@dataclass
class TokenizedChain:
    tokens: list[IsnadToken]
    flags: set[str] = field(default_factory=set)

    @property
    def needs_review(self) -> bool:
        return not self.tokens or bool(self.flags & REVIEW_FLAGS)


# --- cleaning ---------------------------------------------------------------
_FOOTNOTE_MARKER_RE = re.compile(r"[\[(]\s*[0-9٠-٩۰-۹]+\s*[\])]\s*[.:]?")
_ZW_RE = re.compile("[‌‍‎‏]")
_PAREN_RE = re.compile(r"[()\[\]«»]")
_DASH_RE = re.compile(r"[\-–—]+")
_WS_RE = re.compile(r"\s+")


def clean_isnad_text(raw: str) -> str:
    """Normalised, footnote-free, whitespace-collapsed working text.

    Fully normalised (alif/yeh/kaf unified, diacritics stripped) so every
    pattern in this module matches it reliably. Punctuation that carries
    chain structure (، and .) is preserved.
    """
    text = strip_diacritics(raw)
    text = _ZW_RE.sub(" ", text)
    text = _FOOTNOTE_MARKER_RE.sub(" ", text)
    text = _PAREN_RE.sub(" ", text)
    text = _DASH_RE.sub(" ", text)
    text = normalise_arabic_persian(text)
    text = text.replace("،", " ، ").replace(".", " . ")
    return _WS_RE.sub(" ", text).strip()


# --- classification patterns (all literals pass through _n) ------------------
_LONG_HONORIFICS = (
    "عليه السلام",
    "عليها السلام",
    "عليهما السلام",
    "عليهم السلام",
    "صلوات الله عليه وآله",
    "صلوات الله عليهم",
    "صلوات الله عليه",
    "صلى الله عليه وآله وسلم",
    "صلى الله عليه وآله",
)
# Bare ع/ص must be standalone words, or names like «الربيع» become Imams.
_HONORIFIC_ALT = (
    "|".join(_n(h) for h in _LONG_HONORIFICS) + "|" + _n("ع") + "|" + _n("ص")
)
_HONORIFIC_TAIL_RE = re.compile(rf"(?:^|\s)(?:{_HONORIFIC_ALT})\s*[.:،]?\s*$")
_HONORIFIC_INLINE_RE = re.compile(rf"(?:^|\s)(?:{_HONORIFIC_ALT})(?:\s|$)")

_IMAM_TITLES = (
    "رسول الله",
    "النبي",
    "أمير المؤمنين",
    "الصادق",
    "الباقر",
    "الرضا",
    "الكاظم",
    "الجواد",
    "الهادي",
    "العسكري",
    "القائم",
    "صاحب الزمان",
    "أحدهما",
)
_IMAM_NAME_RE = re.compile(
    "^(?:" + "|".join(_n(t) for t in _IMAM_TITLES) + r")(?:\s|$)"
)

_COLLECTIVE_RE = re.compile(
    "^(?:"
    + "|".join(
        _n(h)
        for h in (
            "عدة من أصحابنا",
            "بعض أصحابنا",
            "غير واحد",
            "جماعة من أصحابنا",
            "عدة من رجاله",
        )
    )
    + ")"
)
_UNKNOWN_RE = re.compile(
    "^(?:"
    + _n("رجل من") + r"\s.*"
    + "|" + "|".join(
        _n(h)
        for h in ("رجل", "بعض أصحابه", "بعض رجاله", "من ذكره", "من حدثه", "من رواه", "بعضهم")
    )
    + ")$"
)
_PRONOUN_KINDS = {
    _n("أبيه"): "father",
    _n("أبويه"): "parents",
    _n("جده"): "grandfather",
    _n("أخيه"): "brother",
    _n("عمه"): "uncle",
    _n("عنه"): "anaphora",
    _n("وعنه"): "anaphora",
    _n("بهذا الاسناد"): "same_isnad",
    _n("وبهذا الاسناد"): "same_isnad",
    _n("بهذا الإسناد"): "same_isnad",
}

# --- transmission phrases ---------------------------------------------------
_PHRASES = (
    "عن",
    "حدثنا",
    "حدثني",
    "حدثهم",
    "حدثه",
    "أخبرنا",
    "أخبرني",
    "أخبره",
    "سمعت",
    "سمعنا",
    "رواه",
    "روى",
    "روي",
    "يرفعه",
    "رفعه إلى",
    "رفعه",
    "بإسناده عن",
)
_PHRASE_ALT = "|".join(
    sorted({_n(p) for p in _PHRASES}, key=len, reverse=True)
).replace(" ", r"\s+")
_SPLIT_RE = re.compile(rf"(?:^|\s)(و)?({_PHRASE_ALT})\s+")

_TRAILING_SPEECH_RE = re.compile(
    r"(?:\s|^)" + _n("(?:أنها|أنهما|أنه)?") + r"\s*"
    + _n("(?:قالا|قالت|قال|يقول|سئل)") + r"\s*[:.،]?\s*$"
)
_EMBEDDED_SPEECH_RE = re.compile(r"\s" + _n("(?:قالا|قالت|قال|سمع)") + r"\s")
_ASKED_RE = re.compile(_n("(?:سألت|سألنا|سئلت|سئل|سأل|قلت ل|سمعت|سمع)"))
_CITATION_NOISE_RE = re.compile(
    _n("ج") + r"\s*\d+\s*" + _n("ص") + r"\s*\d+"
    + "|" + _n("في الكافي")
    + "|" + _n("في التهذيب")
    + "|" + _n("في الفقيه")
    + "|" + _n("في بعض النسخ")
)
_RAF_PHRASES = {_n("رفعه"), _n("رفعه إلى"), _n("يرفعه")}
_MURSAL_PHRASES = {_n("روي"), _n("روى"), _n("يروى")}
_DIGIT_RE = re.compile(r"[0-9٠-٩۰-۹]")
_TAHWIL_RE = re.compile(r"\sح(?:\s|$)")
_JAMIAN_RE = re.compile(r"(?:^|\s)" + _n("جميعا") + r"(?=\s|$)")
_PARALLEL_PERIOD_RE = re.compile(
    r"\S\s*\.\s+و?(?=[^.\n]{0,80}(?:^|\s)(?:بن|ابن)(?:\s|$))"
    r"(?=[^.\n]{0,80}(?:^|\s)عن(?:\s|$))"
)

_SCHOLAR_HONORIFIC_RE = re.compile(
    "|".join(
        _n(h)
        for h in ("أيده الله تعالى", "أيده الله", "رحمه الله", "رضي الله عنه", "قدس سره")
    )
)
_LEADING_JUNK_RE = re.compile(
    "^(?:"
    + "|".join(
        _n(w)
        for w in ("و", "ف", "ما", "ثم", "به", "أن", "أنه", "فأما", "أما", "وأما", "فاما", "والخبر الذي")
    )
    + r")\s+"
)
# Classical narrator names that genuinely begin with واو — an attached
# conjunction waw must not be split off these.
_WAW_INITIAL_NAMES_ALT = "|".join(
    _n(w) for w in ("هب", "ليد", "اقد", "ائل", "اصل", "ردان", "هيب")
)
_TRAILING_JUNK_RE = re.compile(
    r"\s(?:" + "|".join(_n(w) for w in ("و", "أنه", "أنها", "أنهما", "ثم")) + r")$"
)


def _strip_leading_junk(text: str) -> str:
    prev = None
    while prev != text:
        prev = text
        text = _LEADING_JUNK_RE.sub("", text).strip(" ،.")
    return text


def _tidy_token(text: str) -> str:
    text = _SCHOLAR_HONORIFIC_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip(" .،:")
    text = _strip_leading_junk(text)
    prev = None
    while prev != text:
        prev = text
        text = _TRAILING_JUNK_RE.sub("", text).strip(" .،:")
    return text


def _is_imam(norm: str) -> bool:
    return bool(_HONORIFIC_TAIL_RE.search(norm)) or bool(_IMAM_NAME_RE.match(norm))


def _classify(raw: str, phrase: str | None) -> IsnadToken | None:
    norm = _tidy_token(raw)
    if not norm or norm in {_n("و"), _n("ما"), _n("ثم"), _n("به"), "،", "."}:
        return None
    if _is_imam(norm):
        kind = "ambiguous" if norm.startswith(_n("أحدهما")) else None
        return IsnadToken(raw=norm, norm=norm, phrase=phrase, node_type=IMAM, relation_kind=kind)
    if norm in _PRONOUN_KINDS:
        return IsnadToken(
            raw=norm, norm=norm, phrase=phrase, node_type=PRONOUN,
            relation_kind=_PRONOUN_KINDS[norm],
        )
    if _COLLECTIVE_RE.match(norm):
        return IsnadToken(raw=norm, norm=norm, phrase=phrase, node_type=COLLECTIVE)
    if _UNKNOWN_RE.match(norm):
        return IsnadToken(raw=norm, norm=norm, phrase=phrase, node_type=UNKNOWN)
    return IsnadToken(raw=norm, norm=norm, phrase=phrase, node_type=NAMED)


def _extract_imam_from_spill(spill: str) -> str | None:
    """Recover «سألت أبا عبد الله عليه السلام ...» -> the Imam token."""
    hit = _HONORIFIC_INLINE_RE.search(spill)
    if not hit:
        return None
    prefix = spill[: hit.end()].strip(" .،:")
    asked = _ASKED_RE.search(prefix)
    if asked:
        prefix = prefix[asked.end():].strip(" .،:")
    # An Imam token is a handful of words, not a sentence.
    if 0 < len(prefix.split()) <= 7:
        return prefix
    return None


@dataclass
class _Segment:
    phrase: str | None
    text: str
    fork: bool  # introduced by «وعن» — a parallel-route marker


def _split_segments(text: str) -> list[_Segment]:
    segments: list[_Segment] = []
    last_end = 0
    phrase: str | None = None
    fork = False
    for match in _SPLIT_RE.finditer(text):
        chunk = text[last_end : match.start()].strip()
        if chunk:
            segments.append(_Segment(phrase=phrase, text=chunk, fork=fork))
        phrase = _WS_RE.sub(" ", match.group(2))
        fork = bool(match.group(1)) and phrase == _n("عن")
        last_end = match.end()
    tail = text[last_end:].strip()
    if tail:
        segments.append(_Segment(phrase=phrase, text=tail, fork=fork))
    return segments


def _co_narrator_parts(segment_text: str) -> list[str]:
    """Split same-tier co-narrators on a top-level «و». Collective phrases
    («عدة من أصحابنا منهم فلان وفلان») are kept whole."""
    if _COLLECTIVE_RE.match(_tidy_token(segment_text)):
        return [segment_text]
    # « و » as a standalone word, «،», or an attached conjunction waw
    # («وحريز», «والحسين»). Guards: never split right after بن/ابن (a واو
    # there is part of a name, e.g. «بن وهب»), and never split off the
    # handful of classical names that genuinely start with واو.
    parts = re.split(
        r"\s+و\s+|\s+،\s+|(?<!بن)\s+و(?!" + _WAW_INITIAL_NAMES_ALT + r")(?=\S)",
        segment_text,
    )
    parts = [p.strip(" ،.") for p in parts if p and p.strip(" ،.")]
    if len(parts) <= 1:
        return [segment_text]
    for part in parts:
        if _DIGIT_RE.search(part) or len(part.split()) > 8:
            return [segment_text]
    return parts


def _special_opening(text: str) -> tuple[list[IsnadToken], set[str]] | None:
    """Faqih-style direct openings, handled before general splitting."""
    stripped = _strip_leading_junk(text)

    m = re.match(_n("قال") + r"\s+(.*)$", stripped)
    if m:
        imam = _extract_imam_from_spill(m.group(1))
        if imam:
            return [IsnadToken(raw=imam, norm=imam, phrase=None, node_type=IMAM)], set()

    m = re.match(_n("سئل") + r"\s+(.*)$", stripped)
    if m:
        imam = _extract_imam_from_spill(m.group(1))
        if imam:
            return (
                [IsnadToken(raw=imam, norm=imam, phrase=None, node_type=IMAM)],
                {"anonymous_questioner"},
            )

    m = re.match(_n("سأل") + r"\s+(.*)$", stripped)
    if m:
        rest = m.group(1)
        imam_start = re.search(
            r"(?:^|\s)(?:" + _n("أبا") + r"\s|" + _n("أبي") + r"\s|"
            + "|".join(_n(t) for t in _IMAM_TITLES) + ")",
            rest,
        )
        if imam_start:
            asker = rest[: imam_start.start()].strip()
            imam = _extract_imam_from_spill(rest[imam_start.start():])
            if imam and asker:
                asker_token = _classify(asker, None)
                if asker_token is not None:
                    return (
                        [asker_token, IsnadToken(raw=imam, norm=imam, phrase=None, node_type=IMAM)],
                        set(),
                    )
    return None


def tokenize_isnad(isnad_raw: str) -> list[TokenizedChain]:
    """Tokenize one hadith's isnad into one or more classified chains."""
    text = clean_isnad_text(isnad_raw)
    global_flags: set[str] = set()

    stripped = _strip_leading_junk(text)
    first_word = stripped.split(" ", 1)[0] if stripped else ""
    if first_word in _MURSAL_PHRASES:
        global_flags.add("mursal_opening")

    special = _special_opening(text)
    if special is not None:
        tokens, flags = special
        return [TokenizedChain(tokens=tokens, flags=flags | global_flags)]

    parts = [p for p in _TAHWIL_RE.split(text) if p.strip()]
    if len(parts) > 1:
        global_flags.add("tahwil")

    chains: list[TokenizedChain] = []
    for part in parts:
        chains.extend(_tokenize_single(part, set(global_flags)))
    if len(chains) > 1:
        for chain in chains:
            chain.flags.add("expanded")
    return chains


def _tokenize_single(text: str, flags: set[str]) -> list[TokenizedChain]:
    text = _strip_leading_junk(text)
    text = _TRAILING_SPEECH_RE.sub("", text).strip()

    if _JAMIAN_RE.search(text):
        flags.add("multi_route")
        text = _WS_RE.sub(" ", _JAMIAN_RE.sub(" ", text)).strip()
    # A mid-isnad period is eShia's usual punctuation for a parallel route
    # («…الصفار. وسعد بن عبد الله عن…»).
    if _PARALLEL_PERIOD_RE.search(text):
        flags.add("multi_route")

    segments = _split_segments(text)
    if any(seg.fork for seg in segments):
        flags.add("multi_route")

    # Same-tier co-narrator alternatives per segment — unless the chain is
    # multi-route, where a «و» may be a route boundary, not a same-tier pair.
    alternatives: list[list[str]] = []
    phrases: list[str | None] = []
    for seg in segments:
        seg_text = _TRAILING_SPEECH_RE.sub("", seg.text).strip(" ،.")
        if seg.phrase in _RAF_PHRASES:
            flags.add("raf")
        if seg.phrase == _n("بإسناده عن"):
            flags.add("compressed_isnad")
        if not seg_text:
            continue
        parts = [seg_text] if "multi_route" in flags else _co_narrator_parts(seg_text)
        alternatives.append(parts)
        phrases.append(seg.phrase)

    total = 1
    for parts in alternatives:
        total *= len(parts)
    if total > MAX_EXPANDED_CHAINS:
        flags.add("co_narrator_cap")
        alternatives = [[parts[0]] for parts in alternatives]
    elif total > 1:
        flags.add("co_narrator_expanded")

    combos: list[list[str]] = [[]]
    for parts in alternatives:
        combos = [combo + [p] for combo in combos for p in parts]

    chains: list[TokenizedChain] = []
    for combo in combos:
        tokens: list[IsnadToken] = []
        chain_flags = set(flags)
        for seg_text, phrase in zip(combo, phrases):
            if _CITATION_NOISE_RE.search(seg_text) or _DIGIT_RE.search(seg_text):
                chain_flags.add("citation_noise")
                continue
            embedded = _EMBEDDED_SPEECH_RE.search(seg_text)
            if embedded:
                head = seg_text[: embedded.start()].strip()
                spill = seg_text[embedded.end():].strip()
                token = _classify(head, phrase) if head else None
                if token is not None:
                    tokens.append(token)
                imam = _extract_imam_from_spill(spill)
                if imam is not None:
                    tokens.append(IsnadToken(raw=imam, norm=imam, phrase=None, node_type=IMAM))
                else:
                    chain_flags.add("matn_spill")
                break
            token = _classify(seg_text, phrase)
            if token is None:
                continue
            if len(token.norm) > 120:
                chain_flags.add("suspicious_token")
            tokens.append(token)
            if token.node_type == IMAM:
                break  # everything after the Imam is topic/matn, not chain
        if tokens and tokens[-1].node_type != IMAM:
            chain_flags.add("no_imam_terminal")
        if not tokens:
            chain_flags.add("no_parseable_chain")
        chains.append(TokenizedChain(tokens=tokens, flags=chain_flags))
    return chains
