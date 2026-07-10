// Segments a crawled eShia page into hadith units, commentary, headings and
// footnotes. Built against the real formatting of all seven core editions:
//
//   al-Kafi (dar al-hadith)   "٢٨ / ٢٨. عِدَّةٌ …"
//   al-Kafi (Islamiyya)       "4- مُحَمَّدُ …"        (western digits)
//   al-Faqih                  "1673- قَالَ …", "3301 وَ- رَوَى …"
//   Wasail al-Shia            "[ ٢٢٠١٥ ] ٧ ـ وعن …"  (serial + sequence)
//   Tahdhib al-Ahkam          "(٥٧٧) ٥١ ـ وروى …"
//   al-Istibsar               "[٥٨٤]" alone, then "٦ ـ فأما ما رواه …"
//   Bihar al-Anwar            "١٣ ـ سن : …" with boundaries MID-LINE after a
//                             period, "بيان :" commentary, and honorifics
//                             encoded as digits (7 = عليه‌السلام, 9 = صلى‌الله…)
//
// Newline semantics in text_raw: \r\n is a soft print-wrap (join with a
// space); \n is a real break but NOT a reliable hadith boundary (it also
// occurs mid-hadith). The trustworthy boundaries are the numbering patterns
// above and footnote markers "[١]"/"[1]" trailing the page.
import type { PageTextBlock } from "@/lib/api/types";

export interface HadithUnit {
  kind: "hadith" | "continuation" | "text" | "heading";
  number?: string;
  isnad?: string;
  matn?: string;
  text?: string;
  notes?: string[];
}

export interface Footnote {
  marker: string;
  text: string;
}

export interface ParsedPage {
  units: HadithUnit[];
  footnotes: Footnote[];
}

const NUM = "[0-9٠-٩]+";
const GAP = "[\\s\\u200c\\u200d]*";
const FIRST_NUM_RE = new RegExp(NUM);
const WASAIL_BOOK_ID = 1306;

// "[ ٢٢٠١٥ ]" / "(٥٧٧)" serial prefix, then "٧" or "٢٨ / ٢٨" sequence,
// then a separator: "ـ" / "-" / "–" / "." — incl. al-Faqih's "3301 وَ- رَوَى".
const HADITH_START_RE = new RegExp(
  `^(?:[\\[(]${GAP}(${NUM})${GAP}[\\])]${GAP}(?:[.]${GAP})?)?(${NUM}(?:${GAP}/${GAP}${NUM})?)${GAP}(?:وَ?${GAP})?[ـ\\-–—.]${GAP}`
);

// "[٥٨٤]" or "(٥٧٧)" alone on a line — a serial that belongs to the next unit.
const BARE_SERIAL_RE = new RegExp(`^[\\[(]\\s*(${NUM})\\s*[\\])]\\s*[.]?$`);

// "[٢٦١] وما كان فيه عن …" — bracketed number followed by prose. Either a
// Wasail mashyakha entry (body) or a footnote — disambiguated in addLine.
// The optional "." / ":" after the bracket covers al-Faqih's "[6]. أي …".
const BRACKET_PROSE_RE = new RegExp(`^\\[\\s*(${NUM})\\s*\\]\\s*[.:]?\\s*(.+)$`);

// "[٢٠١] ٣ عنه عن الحسن..." — al-Istibsar sometimes omits the dash between
// the local sequence number and the isnad.
const BRACKET_SEQ_START_RE = new RegExp(
  `^[\\[(]${GAP}(${NUM})${GAP}[\\])]${GAP}(${NUM})${GAP}(?=(?:عنه|وعن|وبإسناده|وبهذا|وفي)(?=[\\s،ـ\\-]|$))`
);

const BRACKET_DASH_SEQ_START_RE = new RegExp(
  `^[\\[(]${GAP}(${NUM})${GAP}[\\])]${GAP}[ـ\\-–—.]${GAP}(${NUM})${GAP}`
);

const BRACKET_DOUBLE_SERIAL_START_RE = new RegExp(
  `^[\\[(]${GAP}(${NUM})${GAP}[\\])]${GAP}[\\[(]${GAP}(${NUM})${GAP}[\\])]${GAP}(${NUM}(?:${GAP}و${GAP}${NUM})?)${GAP}[ـ\\-–—.]${GAP}`
);

const BRACKET_COLON_RE = new RegExp(`^\\[\\s*${NUM}\\s*\\]\\s*:`);

const DECORATED_BRACKET_HEADING_RE =
  /^(?:["“”]\s*)?(?:\*\s*)?(?:\(\s*)?(?:باب|أبواب)(?=[\s)"*]|$)/;

const BRACKET_APPARATUS_RE =
  /^(?:كما في|من (?:سورة|تفسيره|الباب)|في كتاب|والظاهر|وقال (?:تعالى|سبحانه)|النساء\s*:|الانعام\s*:|أسرى\s*:)/;

const BRACKET_SOURCE_NOTE_RE = /^\(\*\)\s*/;

const WASAIL_BRACKET_START_RE = new RegExp(
  `^\\[${GAP}(${NUM})${GAP}\\]${GAP}(?:[.]${GAP})?(?:(?:و${GAP})?\\[${GAP}(${NUM})${GAP}\\]${GAP})?(.+)$`
);

const WASAIL_LOCAL_SEQ_RE = new RegExp(
  `^(${NUM}(?:${GAP}و${GAP}${NUM})?)${GAP}(?:[ـ\\-–—.]${GAP})?(.+)$`
);

const WASAIL_DASH_BODY_RE = /^[ـ\-–—.]\s*(.+)$/;
const WASAIL_NOTE_RE = /^(?:ورواه|ورواها|رواه|وفي\s*\(|أقول)(?=[\s:：،‌(]|$)/;
const WASAIL_HEADING_RE = /^(?:الباب|أبواب)\s+[0-9٠-٩]+/;

// "(٥٧٧) الاستبصار ج ١ ص ١٦٣" — Tahdhib footnotes. The negative lookahead
// keeps "(٥٧٧) ٥١ ـ وروى…" (a hadith serial + sequence) out of this rule.
const PAREN_FOOTNOTE_RE = new RegExp(
  `^\\(\\s*(${NUM})\\s*\\)\\s*[.:]?\\s+(?!${NUM}\\s*(?:/|[ـ\\-–—.]\\s))(.+)$`
);

// "٧ ـ الكافي ٥ : ٩٢ / ٦." — numbered source-reference line inside the
// footnote zone (Wasail/Istibsar takhrij).
const DASH_FOOTNOTE_RE = new RegExp(`^\\*?\\s*ـ?\\s*(${NUM})\\s*[ـ\\-–—]\\s*(.+)$`);

// "* ـ ١٢٩ ـ التهذيب…" — Istibsar's footnote-zone opener.
const STAR_LINE_RE = /^\*\s*[ـ\-–—]/;

// Looks like an edition citation: "ج ٢", "ص ٣٢٤", "ح ١", "٥ : ٩٢ / ٦",
// "١ : ٤٠٨|١٢٨٥", or a terse source page ref such as "المقنعة : ٥١".
const CITATION_RE =
  /(?:^|[\s،(])(?:ج|ص|ح)\s*[0-9٠-٩]+|[0-9٠-٩]+\s*:\s*[0-9٠-٩]+(?:\s*[\/|]\s*[0-9٠-٩]+)?|[:：]\s*[0-9٠-٩]+/;

// First "he/she said" ends the transmission chain: either "قال :" or "قال"
// followed by the reported speech formula. Kafi often has "قال قال أبو..."
// or "قال لي أبو..." with no colon, so those are explicit boundaries too.
const SPEECH_RE =
  /(?:قَالَ|قَالَتْ|قال|قالت)(?:\s*[:：]|\s+(?=سَمِعْتُ|سمعت|قُلْتُ|قلت|سَأَلْتُ|سألت|كَتَبْتُ|كتبت|قَالَ|قال|فَقَالَ|فقال|يَقُولُ|يقول|لِي|لي|أَبُو|أبو|أَبِي|أبي|أَمِيرُ|أمير|رَسُولُ|رسول|النَّبِيُّ|النبي|عَلِيُّ|علي|الْحَسَنُ|الحسن|الْحُسَيْنُ|الحسين))/;

// Only treat a prefix as an isnad if it actually reads like one.
const ISNAD_HINT_RE = /عَنْ|عن |بْن|بن |حَدَّثَ|أَخْبَرَ|عِدَّة|رَوَى|روى|رويته|بإسناده|بِإِسْنَادِهِ/;
const ISNAD_CONNECTOR_RE = /(?:^|[\s،])(?:عن|عمن|بإسناده|بهذا الإسناد|رفعه)(?=[\s،]|$)/g;

// Commentary/apparatus openers that should break out of a hadith card into a
// plain paragraph (al-Majlisi's بيان, al-Tusi's أقول/فالوجه, takhrij ورواه…).
// NB: JS \b doesn't work adjacent to Arabic letters (they aren't \w), so an
// explicit delimiter lookahead is required.
const COMMENTARY_RE =
  /^(?:بيان|أقول|توضيح|إيضاح|تبيين|تبيان|شرح|فالوجه|فأما ما رواه|قال الشيخ|قال مصنف|ورواه)(?=[\s:：،‌]|$)/;

// Harakat only — tatweel (ـ) must survive because it's the hadith-number
// separator that HEADING_RE's optional numeric prefix matches against.
const HARAKAT_RE = /[ً-ْٰ]/g;
const HEADING_RE = new RegExp(`^(?:[\\[(]?${NUM}[\\])]?\\s*[ـ\\-–—.]\\s*)?(?:كتاب|باب|أبواب)\\s`);

function stripDiacritics(text: string): string {
  return text.replace(HARAKAT_RE, "");
}

function isHeading(line: string): boolean {
  return HEADING_RE.test(stripDiacritics(line));
}

function toArabicDigits(value: string): string {
  return value.replace(/[0-9]/g, (d) => "٠١٢٣٤٥٦٧٨٩"[Number(d)]);
}

function toNumber(value: string): number {
  return Number(value.replace(/[٠-٩]/g, (d) => String("٠١٢٣٤٥٦٧٨٩".indexOf(d))));
}

function firstNumber(value: string): number {
  const match = FIRST_NUM_RE.exec(value);
  return match ? toNumber(match[0]) : Number.NaN;
}

function isFootnoteMarker(value: string): boolean {
  return toNumber(value) <= 50;
}

// eShia's Bihar text encodes honorifics as font glyphs on western digits
// (e.g. "الصادق7", "رسول الله 9"). Expand them so they read as text. Digits
// after volume/page markers (ج/ص/ح) are citations and are left alone.
const DIGIT_HONORIFICS: Record<string, string> = {
  "7": "عليه‌السلام",
  "8": "عليهما‌السلام",
  "9": "صلى‌الله‌عليه‌وآله",
};

function expandDigitHonorifics(text: string): string {
  return text.replace(
    /(?<![جصح])(?<![جصح] )(?<=[؀-ۿ][‌‍]?\s?)([789])(?=[\s.،؛:؟!»)‌]|$)/g,
    (_m, d: string) => ` ${DIGIT_HONORIFICS[d]} `
  );
}

function splitIsnad(text: string): { isnad?: string; matn: string } {
  const match = SPEECH_RE.exec(text);
  if (!match) return { matn: text };
  const end = match.index + match[0].length;
  const isnad = text.slice(0, end).trim();
  const plainIsnad = stripDiacritics(isnad);
  const connectorCount = Array.from(plainIsnad.matchAll(ISNAD_CONNECTOR_RE)).length;
  const hasStrongChain = connectorCount >= 2 || /بإسناده|بهذا الإسناد|عدة من أصحابنا/.test(plainIsnad);
  const boundaryIsLate = match.index > text.length * (hasStrongChain ? 0.82 : 0.6);
  if (boundaryIsLate || isnad.length < 10 || !ISNAD_HINT_RE.test(isnad)) {
    return { matn: text };
  }
  return { isnad, matn: text.slice(end).trim() };
}

function makeNumberLabel(serial: string | null, seq: string): string {
  const cleanSeq = toArabicDigits(seq.replace(/\s+/g, " ").trim());
  if (serial) return `${cleanSeq} / ${toArabicDigits(serial.trim())}`;
  return cleanSeq;
}

function makeSerialRangeLabel(firstSerial: string, secondSerial: string, seq: string): string {
  const cleanSeq = toArabicDigits(seq.replace(/\s+/g, " ").trim());
  return `${cleanSeq} / ${toArabicDigits(firstSerial.trim())}-${toArabicDigits(secondSerial.trim())}`;
}

/** True when `text` ends a sentence — used to decide whether an unnumbered
 * line continues the previous paragraph or starts a new one. */
function endsTerminal(text: string): boolean {
  return /[.؟!»:…]\s*$/.test(text.trim());
}

class PageBuilder {
  units: HadithUnit[] = [];
  footnotes: Footnote[] = [];
  private pendingSerial: string | null = null;
  private inFootnotes = false;

  private takeSerial(): string | null {
    const serial = this.pendingSerial;
    this.pendingSerial = null;
    return serial;
  }

  /** The footnote zone is one-way: once the page's apparatus starts, every
   * remaining line belongs to it (editions restart their markers per hadith,
   * so marker numbering can't be relied on — position can). */
  enterFootnoteZone() {
    this.inFootnotes = true;
  }

  private addFootnoteLine(line: string) {
    const marked =
      BRACKET_PROSE_RE.exec(line) ?? PAREN_FOOTNOTE_RE.exec(line) ?? DASH_FOOTNOTE_RE.exec(line);
    if (marked) {
      this.footnotes.push({ marker: toArabicDigits(marked[1]), text: marked[2].trim() });
    } else if (this.footnotes.length > 0) {
      // Wrapped continuation of the previous footnote.
      this.footnotes[this.footnotes.length - 1].text += ` ${line}`;
    } else {
      this.footnotes.push({ marker: "", text: line });
    }
  }

  addLine(rawLine: string) {
    const line = rawLine.trim();
    if (!line) return;

    if (this.inFootnotes) {
      this.addFootnoteLine(line);
      return;
    }

    const bareSerial = BARE_SERIAL_RE.exec(line);
    if (bareSerial) {
      this.pendingSerial = bareSerial[1];
      return;
    }

    if (isHeading(line)) {
      this.pendingSerial = null;
      this.units.push({ kind: "heading", text: line });
      return;
    }

    // Istibsar opens its apparatus with "* ـ ١٢٩ ـ التهذيب…".
    if (STAR_LINE_RE.test(line)) {
      this.enterFootnoteZone();
      this.addFootnoteLine(line);
      return;
    }

    const bracketDoubleSerialStart = BRACKET_DOUBLE_SERIAL_START_RE.exec(line);
    if (bracketDoubleSerialStart) {
      const rest = line.slice(bracketDoubleSerialStart[0].length).trim();
      this.units.push({
        kind: "hadith",
        number: makeSerialRangeLabel(
          bracketDoubleSerialStart[1],
          bracketDoubleSerialStart[2],
          bracketDoubleSerialStart[3]
        ),
        text: rest,
      });
      return;
    }

    const bracketDashSeqStart = BRACKET_DASH_SEQ_START_RE.exec(line);
    if (bracketDashSeqStart) {
      const rest = line.slice(bracketDashSeqStart[0].length).trim();
      this.units.push({
        kind: "hadith",
        number: makeNumberLabel(bracketDashSeqStart[1], bracketDashSeqStart[2]),
        text: rest,
      });
      return;
    }

    const bracketSeqStart = BRACKET_SEQ_START_RE.exec(line);
    if (bracketSeqStart) {
      const rest = line.slice(bracketSeqStart[0].length).trim();
      this.units.push({
        kind: "hadith",
        number: makeNumberLabel(bracketSeqStart[1], bracketSeqStart[2]),
        text: rest,
      });
      return;
    }

    const hadithStart = HADITH_START_RE.exec(line);
    if (hadithStart) {
      const rest = line.slice(hadithStart[0].length).trim();
      // "٧ ـ الكافي ٥ : ٩٢ / ٦." — a numbered source reference, not a hadith.
      if (!hadithStart[1] && rest.length < 160 && CITATION_RE.test(rest)) {
        this.enterFootnoteZone();
        this.addFootnoteLine(line);
        return;
      }
      const serial = hadithStart[1] ?? this.takeSerial();
      this.units.push({
        kind: "hadith",
        number: makeNumberLabel(serial ?? null, hadithStart[2]),
        text: rest,
      });
      return;
    }

    const bracketProse = BRACKET_PROSE_RE.exec(line);
    if (bracketProse) {
      const marker = bracketProse[1];
      const text = bracketProse[2].trim();
      const plainText = stripDiacritics(text);

      if (!isFootnoteMarker(marker) && DECORATED_BRACKET_HEADING_RE.test(plainText)) {
        this.pendingSerial = null;
        this.units.push({ kind: "heading", text: line });
        return;
      }

      if (!isFootnoteMarker(marker) && BRACKET_SOURCE_NOTE_RE.test(plainText)) {
        this.units.push({ kind: "text", text });
        return;
      }

      // Low bracket markers are footnotes, often printed without a space after
      // the bracket. High bracket markers with colon/reference openers are also
      // apparatus; high Wasail mashyakha/body entries stay in the text.
      if (
        isFootnoteMarker(marker) ||
        BRACKET_COLON_RE.test(line) ||
        CITATION_RE.test(text) ||
        BRACKET_APPARATUS_RE.test(plainText)
      ) {
        this.enterFootnoteZone();
        this.addFootnoteLine(line);
        return;
      }
      this.units.push({
        kind: "hadith",
        number: makeNumberLabel(null, marker),
        text,
      });
      return;
    }

    const parenFootnote = PAREN_FOOTNOTE_RE.exec(line);
    if (parenFootnote) {
      // Tahdhib: "(٥٧٧) الاستبصار ج ١ ص ١٦٣" — serial + citation prose.
      this.enterFootnoteZone();
      this.addFootnoteLine(line);
      return;
    }

    if (COMMENTARY_RE.test(stripDiacritics(line))) {
      this.units.push({ kind: "text", text: line });
      return;
    }

    const current = this.units[this.units.length - 1];
    if (!current || current.kind === "heading") {
      this.units.push({ kind: "text", text: line });
    } else if (current.kind === "hadith" || current.kind === "continuation") {
      // Hadith are atomic until the next recognised boundary.
      current.text = `${current.text ?? ""}\n${line}`.trim();
    } else if (endsTerminal(current.text ?? "")) {
      this.units.push({ kind: "text", text: line });
    } else {
      current.text = `${current.text ?? ""}\n${line}`.trim();
    }
  }

  finalise(): ParsedPage {
    const hasNumbered = this.units.some((u) => u.kind === "hadith");

    for (const [index, unit] of this.units.entries()) {
      if (unit.kind === "heading" || !unit.text) continue;
      const flattened = unit.text.replace(/\n+/g, " ").replace(/\s{2,}/g, " ").trim();

      // A page that opens mid-hadith (before its first numbered unit) is the
      // tail of the previous page's hadith — style it like one.
      if (unit.kind === "text" && index === 0 && hasNumbered && flattened.length > 60) {
        unit.kind = "continuation";
      }

      if (unit.kind === "hadith" || unit.kind === "continuation") {
        const { isnad, matn } = splitIsnad(flattened);
        unit.isnad = isnad;
        unit.matn = matn;
      } else {
        unit.text = flattened;
      }
    }
    return { units: this.units, footnotes: this.footnotes };
  }
}

function parseWasailHadithStart(line: string): { number: string; text: string } | null {
  const match = WASAIL_BRACKET_START_RE.exec(line);
  if (!match || isFootnoteMarker(match[1])) return null;

  const rest = match[3].trim();
  if (!rest || BRACKET_SOURCE_NOTE_RE.test(rest)) return null;

  const secondSerial = match[2] ?? null;
  let seq: string | null = null;
  let body = rest;

  const dashBody = WASAIL_DASH_BODY_RE.exec(rest);
  if (dashBody) {
    body = dashBody[1].trim();
    const localSeq = WASAIL_LOCAL_SEQ_RE.exec(body);
    if (localSeq && firstNumber(localSeq[1]) <= 200) {
      seq = localSeq[1].replace(/\s+/g, " ").trim();
      body = localSeq[2].trim();
    }
  } else {
    const localSeq = WASAIL_LOCAL_SEQ_RE.exec(rest);
    if (localSeq && firstNumber(localSeq[1]) <= 200) {
      seq = localSeq[1].replace(/\s+/g, " ").trim();
      body = localSeq[2].trim();
    }
  }

  if (secondSerial && seq) {
    return { number: makeSerialRangeLabel(match[1], secondSerial, seq), text: body };
  }
  if (seq) return { number: makeNumberLabel(match[1], seq), text: body };
  if (secondSerial) return { number: `${toArabicDigits(match[1])}-${toArabicDigits(secondSerial)}`, text: body };
  return { number: toArabicDigits(match[1]), text: body };
}

class WasailPageBuilder {
  units: HadithUnit[] = [];
  footnotes: Footnote[] = [];
  private inFootnotes = false;
  private sawHadith = false;
  private lastTarget: "unit" | "note" | "text" | null = null;

  enterFootnoteZone() {
    this.inFootnotes = true;
  }

  private currentUnit(): HadithUnit | null {
    const unit = this.units[this.units.length - 1];
    if (!unit || (unit.kind !== "hadith" && unit.kind !== "continuation")) return null;
    return unit;
  }

  private addFootnoteLine(line: string) {
    const marked =
      BRACKET_PROSE_RE.exec(line) ?? PAREN_FOOTNOTE_RE.exec(line) ?? DASH_FOOTNOTE_RE.exec(line);
    if (marked) {
      this.footnotes.push({ marker: toArabicDigits(marked[1]), text: marked[2].trim() });
    } else if (this.footnotes.length > 0) {
      this.footnotes[this.footnotes.length - 1].text += ` ${line}`;
    } else {
      this.footnotes.push({ marker: "", text: line });
    }
  }

  private addNote(line: string) {
    const unit = this.currentUnit();
    if (!unit) {
      if (!this.sawHadith) {
        this.units.push({ kind: "continuation", text: line });
        this.lastTarget = "unit";
        return;
      }
      this.units.push({ kind: "text", text: line });
      this.lastTarget = "text";
      return;
    }
    unit.notes ??= [];
    unit.notes.push(line);
    this.lastTarget = "note";
  }

  private appendToNote(line: string): boolean {
    const unit = this.currentUnit();
    const notes = unit?.notes;
    if (!notes?.length) return false;
    notes[notes.length - 1] = `${notes[notes.length - 1]} ${line}`.trim();
    return true;
  }

  private isFootnoteStart(line: string): boolean {
    const bracket = BRACKET_PROSE_RE.exec(line);
    if (bracket && isFootnoteMarker(bracket[1])) return true;

    const dash = DASH_FOOTNOTE_RE.exec(line);
    return Boolean(dash && CITATION_RE.test(dash[2]));
  }

  addLine(rawLine: string) {
    const line = rawLine.trim();
    if (!line) return;

    if (this.inFootnotes) {
      this.addFootnoteLine(line);
      return;
    }

    const lowBracketContinuation = BRACKET_PROSE_RE.exec(line);
    if (
      lowBracketContinuation &&
      isFootnoteMarker(lowBracketContinuation[1]) &&
      this.currentUnit() &&
      /^(?:قال|فقال|عن)(?=[\s:：،]|$)/.test(stripDiacritics(lowBracketContinuation[2].trim()))
    ) {
      const current = this.currentUnit();
      current!.text = `${current!.text ?? ""}\n${line}`.trim();
      this.lastTarget = "unit";
      return;
    }

    if (this.isFootnoteStart(line)) {
      this.enterFootnoteZone();
      this.addFootnoteLine(line);
      return;
    }

    const hadithStart = parseWasailHadithStart(line);
    if (hadithStart) {
      this.sawHadith = true;
      this.units.push({ kind: "hadith", number: hadithStart.number, text: hadithStart.text });
      this.lastTarget = "unit";
      return;
    }

    const bracketSourceNote = BRACKET_PROSE_RE.exec(line);
    if (bracketSourceNote && !isFootnoteMarker(bracketSourceNote[1]) && BRACKET_SOURCE_NOTE_RE.test(bracketSourceNote[2].trim())) {
      this.addNote(bracketSourceNote[2].trim());
      return;
    }

    const plainLine = stripDiacritics(line);
    if (WASAIL_NOTE_RE.test(plainLine)) {
      this.addNote(line);
      return;
    }

    if (WASAIL_HEADING_RE.test(plainLine)) {
      this.units.push({ kind: "heading", text: line });
      this.lastTarget = "text";
      return;
    }

    if (this.lastTarget === "note" && this.appendToNote(line)) return;

    const current = this.currentUnit();
    if (current) {
      current.text = `${current.text ?? ""}\n${line}`.trim();
      this.lastTarget = "unit";
      return;
    }

    if (!this.sawHadith) {
      this.units.push({ kind: "continuation", text: line });
      this.lastTarget = "unit";
      return;
    }

    const previous = this.units[this.units.length - 1];
    if (previous?.kind === "text" && !endsTerminal(previous.text ?? "")) {
      previous.text = `${previous.text ?? ""}\n${line}`.trim();
    } else {
      this.units.push({ kind: "text", text: line });
    }
    this.lastTarget = "text";
  }

  finalise(): ParsedPage {
    for (const unit of this.units) {
      if (unit.kind === "heading" || !unit.text) continue;
      const flattened = unit.text.replace(/\n+/g, " ").replace(/\s{2,}/g, " ").trim();
      if (unit.kind === "hadith" || unit.kind === "continuation") {
        const { isnad, matn } = splitIsnad(flattened);
        unit.isnad = isnad;
        unit.matn = matn;
      } else {
        unit.text = flattened;
      }
      if (unit.notes?.length) {
        unit.notes = unit.notes.map((note) => note.replace(/\n+/g, " ").replace(/\s{2,}/g, " ").trim());
      }
    }
    return { units: this.units, footnotes: this.footnotes };
  }
}

/** Insert hard breaks where a new hadith/commentary starts mid-line — Bihar
 * runs several numbered hadith together on one physical line. Only breaks
 * after sentence-terminal punctuation, so citations like "ص ١٠٢ ، ح ١" are
 * never split. */
function insertInlineBoundaries(text: string): string {
  const numberBoundary = new RegExp(
    `(?<!\\])([.؟!»:])\\s+(?=(?:[\\[(]\\s*${NUM}\\s*[\\])]\\s*)?${NUM}(?:\\s*/\\s*${NUM})?\\s*(?:وَ?\\s*)?[ـ\\-–—][\\s])`,
    "g"
  );
  const commentaryBoundary = /([.؟!»])\s+(?=(?:بيان|أقول|توضيح|إيضاح|تبيين)\s*[:：])/g;
  return text.replace(numberBoundary, "$1\n").replace(commentaryBoundary, "$1\n");
}

function build(lines: string[]): ParsedPage {
  const builder = new PageBuilder();
  for (const line of lines) builder.addLine(line);
  return builder.finalise();
}

function buildWasail(lines: string[]): ParsedPage {
  const builder = new WasailPageBuilder();
  for (const line of lines) builder.addLine(line);
  return builder.finalise();
}

export function parsePageText(textRaw: string, options: { bookId?: number } = {}): ParsedPage {
  const normalised = insertInlineBoundaries(
    expandDigitHonorifics(textRaw.replace(/\r\n/g, " ").replace(/\r/g, " "))
  ).trim();
  if (options.bookId === WASAIL_BOOK_ID) return buildWasail(normalised.split(/\n+/));
  return build(normalised.split(/\n+/));
}

export function parsePageBlocks(blocks: PageTextBlock[], options: { bookId?: number } = {}): ParsedPage {
  const lines: string[] = [];
  const footnoteLines: string[] = [];
  for (const block of blocks) {
    const text = block.text?.trim();
    if (!text || block.kind === "divider") continue;
    const cleaned = insertInlineBoundaries(expandDigitHonorifics(text.replace(/\r?\n/g, " ")));
    if (block.kind === "footnote") footnoteLines.push(...cleaned.split(/\n+/));
    else lines.push(...cleaned.split(/\n+/));
  }
  if (options.bookId === WASAIL_BOOK_ID) {
    const builder = new WasailPageBuilder();
    for (const line of lines) builder.addLine(line);
    if (footnoteLines.length > 0) {
      builder.enterFootnoteZone();
      for (const line of footnoteLines) builder.addLine(line);
    }
    return builder.finalise();
  }
  const builder = new PageBuilder();
  for (const line of lines) builder.addLine(line);
  if (footnoteLines.length > 0) {
    // The HTML already marked these as footnotes — no zone detection needed.
    builder.enterFootnoteZone();
    for (const line of footnoteLines) builder.addLine(line);
  }
  return builder.finalise();
}
