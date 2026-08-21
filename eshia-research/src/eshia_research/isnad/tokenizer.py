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


# The printed report number sometimes survives into isnad_raw («2553- و روى
# الحلبي…»). It is apparatus, never a narrator, and a digit anywhere in a
# segment used to condemn that segment as citation noise.
_LEADING_REPORT_NUMBER_RE = re.compile(r"^[0-9٠-٩۰-۹]+\s+(?=\S)")


def clean_isnad_text(raw: str) -> str:
    """Normalised, footnote-free, whitespace-collapsed working text.

    Fully normalised (alif/yeh/kaf unified, diacritics stripped) so every
    pattern in this module matches it reliably. Punctuation that carries
    chain structure (، and .) is preserved; «:» is spaced out so a speech
    verb that a colon follows («قال: دخلت…») still ends on a word boundary.
    """
    text = strip_diacritics(raw)
    text = _ZW_RE.sub(" ", text)
    text = _FOOTNOTE_MARKER_RE.sub(" ", text)
    text = _PAREN_RE.sub(" ", text)
    text = _DASH_RE.sub(" ", text)
    text = normalise_arabic_persian(text)
    text = text.replace("،", " ، ").replace(".", " . ").replace(":", " : ")
    text = _WS_RE.sub(" ", text).strip()
    return _LEADING_REPORT_NUMBER_RE.sub("", text)


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
_HONORIFIC_INLINE_RE = re.compile(
    rf"(?:^|\s)(?:{_HONORIFIC_ALT})(?=\s|[.:،]|$)"
)

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
# The word boundary is a *lookbehind*, not a consumed space: «روي عن فلان»
# puts two transmission phrases back to back, and a consumed separator left
# the second one unmatched, so «عن» was kept inside the narrator's token.
_SPLIT_RE = re.compile(rf"(?:^|(?<=\s))(و)?({_PHRASE_ALT})\s+")

_TRAILING_SPEECH_RE = re.compile(
    r"(?:\s|^)" + _n("(?:أنها|أنهما|أنه)?") + r"\s*"
    + _n("(?:قالا|قالت|قال|يقول|سئل)") + r"\s*[:.،]?\s*$"
)
# «أنّ» opens the report as surely as «قال» does («عن يونس بن يعقوب أن رجلا
# كان بهمذان…», «عن أبان أن أبا عبد الله ع قال»); without it the whole matn
# stayed glued to the last narrator's name.
_EMBEDDED_SPEECH_RE = re.compile(
    r"\s" + _n("(?:قالا|قالت|قال|سمع|أنهما|أنها|أنه|أن)") + r"\s"
)
_LEADING_SPEECH_RE = re.compile(
    r"^" + _n("(?:قالا|قالت|قال|سمع|أنهما|أنها|أنه|أن)") + r"\s+"
)
# Formulas a narrator uses to place himself in front of the Ma'sum. What
# follows one of these is the Imam's name; keeping the verb in the token
# («دخلنا على أبي الحسن الرضا ع») leaves a name no person layer can match.
_ASKED_RE = re.compile(
    _n(
        "(?:سألت|سألنا|سئلت|سئل|سأل|قلت ل|سمعت|سمع"
        "|دخلت على|دخلنا على|كنت عند|كنا عند|أتي|أتى)"
    )
)
_CITATION_NOISE_RE = re.compile(
    _n("ج") + r"\s*\d+\s*" + _n("ص") + r"\s*\d+"
    + "|" + _n("في الكافي")
    + "|" + _n("في التهذيب")
    + "|" + _n("في الفقيه")
    + "|" + _n("في بعض النسخ")
)
# What the tokenizer discards after a speech verb is matn by design. It is
# only worth a human's time when it opens with transmission structure — a
# phrase followed by something to transmit from — because that is the one
# shape in which a narrator could have been dropped.
_CHAIN_CONTINUATION_RE = re.compile(rf"^(?:{_n('و')}\s*)?(?:{_PHRASE_ALT})\s+\S")
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
        for w in (
            "و", "ف", "ما", "ثم", "به", "أن", "أنه", "قد",
            "فأما", "أما", "وأما", "فاما", "والخبر الذي",
        )
    )
    + r")\s+"
)
# Tokens whose leading واو is part of the word, not a conjunction: classical
# names that genuinely begin with واو, and «ولد», the kinship noun that binds
# a mawla to a household («سلمى مولاة ولد أبي عبد الله ع»).
_WAW_INITIAL_NAMES_ALT = "|".join(
    _n(w) for w in ("هب", "ليد", "اقد", "ائل", "اصل", "ردان", "هيب", "لد")
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


# A token that is nothing but a particle or the report's own verb names no
# one — «رفعه قال: إن موسى ع…» must not leave «قال» standing as a narrator.
_NOT_A_NAME = {
    _n(w)
    for w in (
        "و", "ما", "ثم", "به", "قد", "أن", "أنه", "أنها", "أنهما",
        "قال", "قالا", "قالت", "يقول", "سئل", "جميعا",
    )
} | {"،", "."}


# Function words that cannot occur inside an Arabic personal name. A long
# token used to be caught by a 120-character rule, but once «أنّ» became a
# matn boundary the leftovers came in under it and passed silently — and a
# genuine nasab («موسى بن محمد بن القاسم بن حمزة بن موسى بن جعفر») is long
# too, so length was never the thing that distinguished them.
_NON_NAME_WORDS = {
    _n(w)
    for w in (
        "إذا", "الذي", "التي", "الذين", "ذلك", "هذا", "هذه", "ثم", "لكن",
        "حتى", "عند", "بعد", "قبل", "بين", "لما", "حين", "كيف", "أين",
        "إلى", "فيه", "فيها", "له", "لهم", "كان", "كانت", "يكون",
    )
}
# «على» is deliberately absent: normalisation folds alif maqsura into yeh, so
# the preposition and the name «عليّ» are the same string by the time this
# runs. It would condemn every chain through Ali b. Ibrahim.


def _looks_like_matn(norm: str) -> bool:
    return bool(_NON_NAME_WORDS.intersection(norm.split())) or len(norm) > 120


def _classify(raw: str, phrase: str | None) -> IsnadToken | None:
    norm = _tidy_token(raw)
    if not norm or norm in _NOT_A_NAME:
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


def _matn_boundary(text: str, *, allow_honorific: bool = True) -> int:
    """Index at which this segment stops being isnad and becomes matn.

    Two things end a name: the report's opening verb («قال», «أنّ») and the
    honorific that closes a Ma'sum's name and is followed by more words. The
    earlier of the two wins; with neither, the whole segment is still name.

    The honorific only reads as the end of a *name* in a segment some
    transmission phrase introduced. A report al-Saduq opens with narrative
    and no chain at all («و كنّ نساء النبي ص إذا كان عليهنّ صيام…») would
    otherwise yield a tidy four-word Imam node and lose its review flag,
    which is the one case here where saying nothing is the honest answer.
    """
    bounds = []
    speech = _EMBEDDED_SPEECH_RE.search(text)
    if speech:
        bounds.append(speech.start())
    if allow_honorific:
        honorific = _HONORIFIC_INLINE_RE.search(text)
        if honorific and text[honorific.end():].strip(" .،:"):
            bounds.append(honorific.end())
    return min(bounds) if bounds else len(text)


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
        # Two phrases can sit back to back («رفعه عن أبي عبد الله ع»). The
        # empty segment between them still has to be emitted: it is the only
        # carrier of «رفعه», and dropping it lost the raf marker entirely.
        if chunk or phrase is not None:
            segments.append(_Segment(phrase=phrase, text=chunk, fork=fork))
        phrase = _WS_RE.sub(" ", match.group(2))
        fork = bool(match.group(1)) and phrase == _n("عن")
        last_end = match.end()
    tail = text[last_end:].strip()
    if tail:
        segments.append(_Segment(phrase=phrase, text=tail, fork=fork))
    return segments


def _co_narrator_parts(segment_text: str, *, allow_honorific: bool = True) -> list[str]:
    """Split same-tier co-narrators on a top-level «و». Collective phrases
    («عدة من أصحابنا منهم فلان وفلان») are kept whole."""
    if _COLLECTIVE_RE.match(_tidy_token(segment_text)):
        return [segment_text]
    # Past the matn boundary «و» joins clauses («مات و أوصى إلى رجل و له ابن
    # صغير», «في قول الله عز و جل و لا تركنوا…») and would otherwise expand
    # into a chain per clause. Only the name before it can carry co-narrators;
    # each alternative is given the same tail back so the boundary is still
    # there for the caller to act on.
    boundary = _matn_boundary(segment_text, allow_honorific=allow_honorific)
    head, tail = segment_text[:boundary], segment_text[boundary:]
    # « و » as a standalone word, «،», or an attached conjunction waw
    # («وحريز», «والحسين»). Guards: never split right after بن/ابن (a واو
    # there is part of a name, e.g. «بن وهب»), and never split off the
    # handful of classical names that genuinely start with واو.
    parts = re.split(
        r"\s+و\s+|\s+،\s+|(?<!بن)\s+و(?!" + _WAW_INITIAL_NAMES_ALT + r")(?=\S)",
        head,
    )
    parts = [p.strip(" ،.") for p in parts if p and p.strip(" ،.")]
    if len(parts) <= 1:
        return [segment_text]
    for part in parts:
        if _DIGIT_RE.search(part) or len(part.split()) > 8:
            return [segment_text]
    return [part + tail for part in parts]


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

    # Faqih often splits consecutive questions into distinct reports with
    # «سأله [فلان] عن ...». The object pronoun is the Imam named in the
    # preceding report; everything after عن is the question, not isnad.
    m = re.match(
        _n("سأله") + r"(?:\s+(.*?))?\s+" + _n("عن") + r"(?:\s|$)",
        stripped,
    )
    if m:
        tokens: list[IsnadToken] = []
        asker = (m.group(1) or "").strip()
        if asker:
            asker_token = _classify(asker, None)
            if asker_token is not None:
                tokens.append(asker_token)
        tokens.append(
            IsnadToken(
                raw=_n("سأله"),
                norm=_n("سأله"),
                phrase=None,
                node_type=PRONOUN,
                relation_kind="previous_hadith_imam",
            )
        )
        return tokens, set()

    m = re.match(_n("سأل") + r"\s+(.*)$", stripped)
    if m:
        rest = m.group(1)
        brother = re.search(r"\s+" + _n("أخاه") + r"\s+", rest)
        if brother:
            asker = rest[: brother.start()].strip()
            imam = _extract_imam_from_spill(rest[brother.end():])
            if imam and asker:
                asker_token = _classify(asker, None)
                if asker_token is not None:
                    return (
                        [asker_token, IsnadToken(raw=imam, norm=imam, phrase=None, node_type=IMAM)],
                        set(),
                    )
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

    # «جميعا» marks a convergence only while the text is still isnad. Past the
    # matn boundary it is an ordinary adverb («فأكلوا جميعاً», «فولدتا جميعاً
    # في ليلة واحدة») and flagging on it cost those reports their expansion
    # and their review status for nothing.
    jamian = _JAMIAN_RE.search(text)
    if jamian and jamian.start() < _matn_boundary(text):
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
        parts = (
            [seg_text]
            if "multi_route" in flags
            else _co_narrator_parts(seg_text, allow_honorific=seg.phrase is not None)
        )
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
            boundary = _matn_boundary(seg_text, allow_honorific=phrase is not None)
            if boundary < len(seg_text):
                head = seg_text[:boundary].strip()
                spill = _LEADING_SPEECH_RE.sub("", seg_text[boundary:].strip(" .،:"))
                token = _classify(head, phrase) if head else None
                if token is not None:
                    if _looks_like_matn(token.norm):
                        chain_flags.add("suspicious_token")
                    tokens.append(token)
                if token is not None and token.node_type == IMAM:
                    # The chain already reached the Ma'sum; the rest is matn,
                    # and a second honorific in it belongs to the story
                    # («كان لرجل على عهد علي ع جاريتان»), not to the isnad.
                    break
                imam = _extract_imam_from_spill(spill)
                if imam is not None:
                    tokens.append(IsnadToken(raw=imam, norm=imam, phrase=None, node_type=IMAM))
                elif _CHAIN_CONTINUATION_RE.match(spill):
                    chain_flags.add("matn_spill")
                break
            token = _classify(seg_text, phrase)
            if token is None:
                continue
            if _looks_like_matn(token.norm):
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
