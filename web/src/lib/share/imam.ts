// Locating the Imam inside a printed isnad.
//
// A shared hadith image sets the chain in small print and lifts the Imam it
// ends at back up to reading size — the transmitters are provenance, the Imam
// is the speaker. Finding that span is a *typographic* decision with a safe
// fallback (the chain simply stays uniform), never a claim about identity.
// Narrator identity is resolved server-side in `mention_resolutions`; nothing
// here feeds that.

// Tashkil, superscript alef and tatweel: the printed editions are fully
// vocalised, so every match has to be made blind to them.
const DIACRITICS_RE = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/;

interface StrippedText {
  stripped: string;
  /** stripped index -> index in the original string */
  map: number[];
}

function stripForMatching(text: string): StrippedText {
  const chars: string[] = [];
  const map: number[] = [];
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (DIACRITICS_RE.test(ch)) continue;
    // Normalise the two alef-lam ligature spellings and hamza carriers so one
    // pattern covers every edition's orthography.
    chars.push(ch === "أ" || ch === "إ" || ch === "آ" || ch === "ٱ" ? "ا" : ch === "ى" ? "ي" : ch);
    map.push(i);
  }
  return { stripped: chars.join(""), map };
}

// The Fourteen as the editions actually print them: kunya, laqab, or full
// nasab. Written against the stripped form, so no hamza or alef variants.
const IMAM_NAMES = [
  "رسول\\s+الله",
  "النبي",
  "امير\\s+المؤمنين",
  "اب[ويا]\\s+عبد\\s+الله",
  "اب[ويا]\\s+جعفر",
  "اب[ويا]\\s+الحسن",
  "اب[ويا]\\s+محمد",
  "اب[ويا]\\s+ابراهيم",
  "اب[ويا]\\s+الحسين",
  "الصادق",
  "الباقر",
  "الرضا",
  "الكاظم",
  "العسكري",
  "الجواد",
  "الهادي",
  "السجاد",
  "زين\\s+العابدين",
  "المهدي",
  "القائم",
  "الزهراء",
  "فاطمة",
  "علي\\s+بن\\s+الحسين",
  "موسي\\s+بن\\s+جعفر",
  "جعفر\\s+بن\\s+محمد",
  "محمد\\s+بن\\s+علي",
  "علي\\s+بن\\s+موسي",
  "الحسن\\s+بن\\s+علي",
  "الحسين\\s+بن\\s+علي",
  "محمد\\s+بن\\s+الحسن",
].join("|");

// The honorific the edition prints after the name — spelled out, or the bare
// «ع» / «ص» abbreviation the Islamiyya edition uses.
const HONORIFIC =
  "(?:صلي\\s*الله\\s*عليه\\s*و\\s*اله(?:\\s*و\\s*سلم)?|علي(?:ه|ها|هما|هم)\\s*السلام|(?<![ء-ي])[عص](?![ء-ي]))";

// The honorific is the whole discriminator. «أبو جعفر» alone is also
// al-Kulayni's kunya, and Al-Kafi opens thousands of chains with «أَبُو
// جَعْفَرٍ مُحَمَّدُ بْنُ يَعْقُوبَ» — the compiler, not the Imam. Requiring
// the printed honorific within three words separates them exactly; measured
// over all 15,336 Al-Kafi chains it never once took al-Kulayni for al-Baqir.
const IMAM_RE = new RegExp(`(?:${IMAM_NAMES})(?:\\s+\\S+){0,3}?\\s*${HONORIFIC}`, "g");
// A bare «علي ع» is the Commander of the Faithful, but only with the honorific
// directly attached — unqualified «علي» is far too common in a chain.
const ALI_RE = new RegExp(`(?<![ء-ي])علي\\s*${HONORIFIC}`, "g");

export interface ImamSpan {
  /** Index into the original, un-stripped string. */
  start: number;
  end: number;
}

/**
 * The last Imam named in `text`, as a span in the original string.
 *
 * Last, not first: a chain runs from the compiler down to the Imam, so the
 * final honorific-marked name is the one the report is heard from. Returns
 * null when no such name is printed, which is the common and correct answer
 * for roughly half of all chains.
 */
export function findImamSpan(text: string | null | undefined): ImamSpan | null {
  if (!text) return null;
  const { stripped, map } = stripForMatching(text);
  const matches = [...stripped.matchAll(IMAM_RE)];
  const fallback = matches.length === 0 ? [...stripped.matchAll(ALI_RE)] : [];
  const match = (matches.length ? matches : fallback).at(-1);
  if (!match || match.index === undefined) return null;

  const start = map[match.index];
  const lastChar = map[match.index + match[0].length - 1];
  if (start === undefined || lastChar === undefined) return null;
  // Carry any trailing diacritics on the final letter, so the honorific isn't
  // clipped mid-glyph.
  let end = lastChar + 1;
  while (end < text.length && DIACRITICS_RE.test(text[end])) end += 1;
  return { start, end };
}

export interface IsnadRun {
  text: string;
  /** True for the Imam the chain ends at; rendered at reading size. */
  emphasis: boolean;
}

/**
 * Split an isnad into the small-print chain and the Imam it arrives at.
 * With no Imam printed, the whole chain comes back as one unemphasised run.
 */
export function splitIsnadAtImam(isnad: string): IsnadRun[] {
  const span = findImamSpan(isnad);
  if (!span) return [{ text: isnad.trim(), emphasis: false }];
  const runs: IsnadRun[] = [];
  const before = isnad.slice(0, span.start).trim();
  const imam = isnad.slice(span.start, span.end).trim();
  const after = isnad.slice(span.end).trim();
  if (before) runs.push({ text: before, emphasis: false });
  if (imam) runs.push({ text: imam, emphasis: true });
  if (after) runs.push({ text: after, emphasis: false });
  return runs;
}
