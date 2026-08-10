// Rendering a hadith to a shareable image.
//
// Canvas 2D rather than a DOM-rasteriser: the whole job here is Arabic line
// breaking, mixed-size inline runs and optical justification, which is exactly
// the part html-to-image libraries do worst — and it costs no new dependency.
//
// The frame is the `.research-folio` from the homepage — hairline border, inset
// second rule, hard offset shadow, bronze for bibliography — dressed as a
// manuscript page. That motif already means "source record" in this product, so
// a shared image is recognisably Usul16 without a watermark stamped on it.
//
// Nothing on the image evaluates the narration. It states where the text was
// printed and links back to the record; grading is the reader page's job, and a
// badge here would be read as a verdict.

import type { ShareCard, ShareLanguage } from "@/lib/share/card";
import {
  drawCornerPieces,
  drawGirihField,
  drawGrain,
  drawManuscriptFrame,
  drawRosetteDivider,
  drawStarMark,
} from "@/lib/share/ornament";

export type ShareFormat = "square" | "portrait" | "story";

export const SHARE_FORMATS: {
  value: ShareFormat;
  label: string;
  hint: string;
  width: number;
  height: number;
}[] = [
  { value: "square", label: "Square", hint: "1080 × 1080", width: 1080, height: 1080 },
  { value: "portrait", label: "Portrait", hint: "1080 × 1350", width: 1080, height: 1350 },
  { value: "story", label: "Story", hint: "1080 × 1920", width: 1080, height: 1920 },
];

export interface ShareTheme {
  background: string;
  surface: string;
  ink: string;
  muted: string;
  accent: string;
  bronze: string;
  line: string;
  shadow: string;
}

export interface ShareFonts {
  /** next/font family stack for Amiri. */
  arabic: string;
  /** Latin body face. */
  sans: string;
  /** Latin display face, used when English carries the narration. */
  serif: string;
}

interface Font {
  family: string;
  size: number;
  weight: number;
}

interface Run {
  text: string;
  font: Font;
  color: string;
}

interface PlacedWord {
  text: string;
  font: Font;
  color: string;
  width: number;
  overhangLeft: number;
  overhangRight: number;
}

interface Line {
  words: PlacedWord[];
  height: number;
  /** Sum of the word widths, with no inter-word space. */
  inkWidth: number;
  /** Sum of the natural gaps between those words. */
  gapWidth: number;
}

interface Excerpt<T> {
  value: T;
  truncated: boolean;
}

const RTL = "rtl";
const LTR = "ltr";

function fontString(font: Font): string {
  return `${font.weight} ${font.size}px ${font.family}`;
}

function excerptText(text: string, maxWords: number): Excerpt<string> {
  const words = text.trim().split(/\s+/).filter(Boolean);
  if (words.length <= maxWords) return { value: text, truncated: false };
  return { value: `${words.slice(0, maxWords).join(" ")} …`, truncated: true };
}

function excerptRuns(
  runs: ShareCard["isnadRuns"],
  maxWords: number
): Excerpt<ShareCard["isnadRuns"]> {
  const value: ShareCard["isnadRuns"] = [];
  let remaining = maxWords;
  let truncated = false;

  for (const run of runs) {
    const words = run.text.trim().split(/\s+/).filter(Boolean);
    if (!words.length) continue;
    if (remaining <= 0) {
      truncated = true;
      break;
    }
    if (words.length > remaining) {
      value.push({ ...run, text: `${words.slice(0, remaining).join(" ")} …` });
      truncated = true;
      break;
    }
    value.push(run);
    remaining -= words.length;
  }

  if (!truncated && value.length < runs.filter((run) => run.text.trim()).length) {
    truncated = true;
  }
  return { value, truncated };
}

/**
 * Resolve the reader's live theme tokens into colours canvas can paint.
 *
 * The tokens are authored in OKLCH; reading them back through `getComputedStyle`
 * hands us whatever serialisation this browser uses, which is by definition a
 * serialisation the same browser's canvas can parse.
 */
export function readTheme(root: HTMLElement = document.documentElement): ShareTheme {
  const probe = document.createElement("span");
  probe.style.display = "none";
  root.appendChild(probe);
  const resolve = (token: string, fallback: string): string => {
    probe.style.color = "";
    probe.style.color = `var(${token})`;
    const value = getComputedStyle(probe).color;
    return value && value !== "rgba(0, 0, 0, 0)" ? value : fallback;
  };
  const theme: ShareTheme = {
    background: resolve("--background", "#f4eee1"),
    surface: resolve("--folio-bg", "#fbf6ec"),
    ink: resolve("--folio-ink", "#20302a"),
    muted: resolve("--folio-muted", "#5a6660"),
    accent: resolve("--accent", "#3f7a63"),
    bronze: resolve("--folio-accent", "#7a5c33"),
    line: resolve("--folio-line", "#ddd5c4"),
    shadow: resolve("--folio-shadow", "rgba(32, 48, 42, 0.12)"),
  };
  probe.remove();
  return theme;
}

/**
 * The faces the page actually loaded, read from the `next/font` variables on
 * `<html>`.
 *
 * `--font-body` / `--font-display` rather than `--font-sans` / `--font-serif`:
 * the latter are remapped to Amiri under an Arabic interface, and an English
 * translation still has to be set in a Latin face.
 */
export function readFonts(root: HTMLElement = document.documentElement): ShareFonts {
  const styles = getComputedStyle(root);
  const read = (token: string, fallback: string): string => {
    const value = styles.getPropertyValue(token).trim();
    return value ? `${value}, ${fallback}` : fallback;
  };
  return {
    arabic: read("--font-amiri", "Amiri, serif"),
    sans: read("--font-body", "system-ui, sans-serif"),
    serif: read("--font-display", "Georgia, serif"),
  };
}

/**
 * Is this a dark surface?
 *
 * The theme tokens come back in whatever colour syntax the browser serialises
 * OKLCH to, so rather than parse them, paint one pixel and read its luminance.
 */
export function isDark(color: string): boolean {
  const probe = document.createElement("canvas");
  probe.width = 1;
  probe.height = 1;
  const ctx = probe.getContext("2d", { willReadFrequently: true });
  if (!ctx) return false;
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, 1, 1);
  const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 < 0.5;
}

/**
 * Ask the browser to have every face we draw with actually loaded.
 *
 * FontFaceSet.load() normally settles quickly, but it may remain pending when
 * a browser extension, an interrupted font request, or a stale dev-server
 * asset blocks a font. A repost preview must not remain an empty placeholder
 * in that case: canvas can draw with the declared fallback family, so wait a
 * short bounded interval and then render.
 */
export async function ensureFonts(fonts: ShareFonts): Promise<void> {
  if (!("fonts" in document)) return;
  const specimens = [
    `400 72px ${fonts.arabic}`,
    `400 32px ${fonts.sans}`,
    `600 32px ${fonts.sans}`,
    `600 48px ${fonts.serif}`,
  ];
  const fontLoads = Promise.all(
    specimens.map((spec) => document.fonts.load(spec).catch(() => undefined))
  ).then(() => undefined);
  let timeoutId: number | undefined;
  const timeout = new Promise<void>((resolve) => {
    timeoutId = window.setTimeout(resolve, 400);
  });
  await Promise.race([fontLoads, timeout]);
  if (timeoutId !== undefined) window.clearTimeout(timeoutId);
}

interface Metrics {
  /** Advance width — how far the pen moves. */
  advance: number;
  /** Ink poking out past the advance box, left and right. */
  overhangLeft: number;
  overhangRight: number;
}

/** `measureText` dominates the fitting search, and the same words are measured
 * at the same sizes on every pass, so memoise it per render. */
function createMeasurer(ctx: CanvasRenderingContext2D) {
  const cache = new Map<string, Metrics>();
  return (font: Font, text: string): Metrics => {
    const key = `${font.weight}|${font.size}|${font.family}|${text}`;
    const hit = cache.get(key);
    if (hit) return hit;
    ctx.font = fontString(font);
    const m = ctx.measureText(text);
    const metrics: Metrics = {
      advance: m.width,
      overhangLeft: Math.max(0, m.actualBoundingBoxLeft ?? 0),
      overhangRight: Math.max(0, (m.actualBoundingBoxRight ?? 0) - m.width),
    };
    cache.set(key, metrics);
    return metrics;
  };
}

type Measurer = ReturnType<typeof createMeasurer>;

function spaceWidth(measure: Measurer, font: Font): number {
  return measure(font, " ").advance;
}

/**
 * Advance to leave between two adjacent words so their *ink* is a space apart.
 *
 * Two things break a naive advance-width space here. The isnad mixes 25px
 * chain with 38px Imam on one line, so a gap sized in the small face is too
 * tight for the large one. And Amiri's isolated «ع» — the honorific that ends
 * almost every chain — inks about 36% wider than it advances, so its tail
 * reaches back into the space and touches the name before it. Measured on the
 * real text at 152px: 44px of nominal space collapsed to 0.46px of clearance.
 *
 * `earlier` is the word already placed and `later` the one about to be, in
 * reading order; which physical side each overhang faces depends on direction.
 */
function naturalGap(
  measure: Measurer,
  earlier: PlacedWord,
  later: PlacedWord,
  direction: "rtl" | "ltr"
): number {
  const space = Math.max(spaceWidth(measure, earlier.font), spaceWidth(measure, later.font));
  const facing =
    direction === RTL
      ? earlier.overhangLeft + later.overhangRight
      : earlier.overhangRight + later.overhangLeft;
  return space + facing;
}

/** Greedy line breaker over runs that may each carry their own size. */
function layoutRuns(
  measure: Measurer,
  runs: Run[],
  maxWidth: number,
  lineHeight: number,
  direction: "rtl" | "ltr"
): Line[] {
  const lines: Line[] = [];
  let words: PlacedWord[] = [];
  let inkWidth = 0;
  let gapWidth = 0;

  const flush = () => {
    if (!words.length) return;
    const tallest = Math.max(...words.map((word) => word.font.size));
    lines.push({ words, height: tallest * lineHeight, inkWidth, gapWidth });
    words = [];
    inkWidth = 0;
    gapWidth = 0;
  };

  for (const run of runs) {
    for (const token of run.text.split(/\s+/).filter(Boolean)) {
      const metrics = measure(run.font, token);
      const word: PlacedWord = {
        text: token,
        font: run.font,
        color: run.color,
        width: metrics.advance,
        overhangLeft: metrics.overhangLeft,
        overhangRight: metrics.overhangRight,
      };
      const gap = words.length
        ? naturalGap(measure, words[words.length - 1], word, direction)
        : 0;
      if (words.length && inkWidth + gapWidth + gap + word.width > maxWidth) {
        flush();
        words.push(word);
        inkWidth = word.width;
      } else {
        words.push(word);
        inkWidth += word.width;
        gapWidth += gap;
      }
    }
  }
  flush();
  return lines;
}

function linesHeight(lines: Line[]): number {
  return lines.reduce((total, line) => total + line.height, 0);
}

/**
 * Draw one broken block.
 *
 * Justification stretches the inter-word gaps only while they stay believable;
 * past 1.85× the natural space the line goes ragged instead, because rivers of
 * white running down a page of scripture look like a bug, not a choice.
 */
function drawLines(
  ctx: CanvasRenderingContext2D,
  measure: Measurer,
  lines: Line[],
  options: {
    left: number;
    top: number;
    width: number;
    direction: "rtl" | "ltr";
    justify?: boolean;
  }
): number {
  const { left, top, width, direction, justify = false } = options;
  let y = top;

  lines.forEach((line, index) => {
    const baseline = y + line.height * 0.74;
    const gaps = line.words.length - 1;
    const isLast = index === lines.length - 1;
    ctx.direction = direction;
    ctx.textAlign = "left";

    // Justification widens every gap by the same amount, and only while the
    // result stays believable; past half again of the natural space the line
    // goes ragged, because rivers of white running down a page of scripture
    // read as a bug, not as a choice. At display sizes the tell is a line
    // whose word gaps are visibly looser than its neighbour's.
    // Justification needs enough gaps to hide in. A display line carrying four
    // words divides its slack three ways, and the result is visibly looser than
    // the line above it — so below five gaps the line stays ragged, which is
    // how display Arabic is set anyway.
    let stretch = 0;
    if (justify && !isLast && gaps >= 5) {
      const slack = width - line.inkWidth - line.gapWidth;
      const perGap = slack / gaps;
      if (perGap > 0 && perGap <= (line.gapWidth / gaps) * 0.35) stretch = perGap;
    }

    // RTL sets the first word flush right and walks leftwards; LTR is the
    // mirror. Positioning word by word is what lets sizes mix inside a line.
    let cursor = direction === RTL ? left + width : left;
    line.words.forEach((word, wordIndex) => {
      ctx.font = fontString(word.font);
      ctx.fillStyle = word.color;
      ctx.fillText(word.text, direction === RTL ? cursor - word.width : cursor, baseline);
      const next = line.words[wordIndex + 1];
      const advance =
        word.width + (next ? naturalGap(measure, word, next, direction) + stretch : 0);
      cursor += direction === RTL ? -advance : advance;
    });
    y += line.height;
  });

  return y - top;
}

/** Trim to fit, so a long kitab name never runs under the permalink block. */
function ellipsize(
  measure: Measurer,
  font: Font,
  text: string,
  maxWidth: number
): string {
  if (measure(font, text).advance <= maxWidth) return text;
  const words = text.split(/\s+/);
  for (let keep = words.length - 1; keep > 0; keep -= 1) {
    const candidate = `${words.slice(0, keep).join(" ")}…`;
    if (measure(font, candidate).advance <= maxWidth) return candidate;
  }
  return "…";
}

function drawRule(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  color: string
): void {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(x, y + 0.5);
  ctx.lineTo(x + width, y + 0.5);
  ctx.stroke();
  ctx.restore();
}

interface Block {
  lines: Line[];
  direction: "rtl" | "ltr";
  justify: boolean;
  /** Space above this block when it follows another. */
  spaceBefore: number;
  rule?: "hairline" | "rosette";
}

const RULE_GAP = 26;
const ROSETTE_GAP = 42;

function ruleHeight(block: Block): number {
  if (block.rule === "rosette") return ROSETTE_GAP;
  return block.rule ? RULE_GAP : 0;
}

function blocksHeight(blocks: Block[]): number {
  return blocks.reduce(
    (total, block) => total + block.spaceBefore + ruleHeight(block) + linesHeight(block.lines),
    0
  );
}

export interface RenderOptions {
  card: ShareCard;
  language: ShareLanguage;
  format: ShareFormat;
  theme: ShareTheme;
  fonts: ShareFonts;
}

export interface RenderResult {
  canvas: HTMLCanvasElement;
  /** True when the narration was too long to set legibly and was cut short. */
  truncated: boolean;
}

const MOUNT = 70;
const PAD_X = 58;
const PAD_Y = 54;
const SHADOW = 12;
const ARABIC_MIN = 34;
const ARABIC_MAX = 56;
const ENGLISH_LEAD_MIN = 26;
const ENGLISH_LEAD_MAX = 46;
const ENGLISH_SUB_MIN = 20;
const ENGLISH_SUB_MAX = 34;

export function renderShareImage(options: RenderOptions): RenderResult {
  const { card, language, format, theme, fonts } = options;
  const spec = SHARE_FORMATS.find((f) => f.value === format) ?? SHARE_FORMATS[0];
  const canvas = document.createElement("canvas");
  canvas.width = spec.width;
  canvas.height = spec.height;
  const ctx = canvas.getContext("2d", { alpha: false });
  if (!ctx) throw new Error("Canvas 2D is unavailable in this browser");
  ctx.textBaseline = "alphabetic";
  const measure = createMeasurer(ctx);

  const cardX = MOUNT;
  const cardY = MOUNT;
  const cardW = spec.width - MOUNT * 2 - SHADOW;
  const cardH = spec.height - MOUNT * 2 - SHADOW;
  const contentX = cardX + PAD_X;
  const contentW = cardW - PAD_X * 2;

  const arabic = (size: number, weight = 400): Font => ({ family: fonts.arabic, size, weight });
  const sans = (size: number, weight = 400): Font => ({ family: fonts.sans, size, weight });
  const serif = (size: number, weight = 600): Font => ({ family: fonts.serif, size, weight });

  const showArabic = language !== "en";
  const englishLeads = language === "en" && card.english !== null;
  const showEnglish = language !== "ar" && card.english !== null;

  // A social card can only display a bounded excerpt. Measuring thousands of
  // words before discovering that fact freezes the main thread on slower
  // phones, and timers cannot interrupt synchronous canvas work. Cap the
  // candidate text before the first measureText call. Taller formats earn a
  // larger budget; bilingual cards split it between the two narrations.
  const totalNarrativeBudget = spec.height >= 1900 ? 210 : spec.height >= 1300 ? 144 : 112;
  const narrativeSlots = Math.max(1, Number(showArabic) + Number(showEnglish));
  const perNarrativeBudget = Math.max(64, Math.floor(totalNarrativeBudget / narrativeSlots));
  const matnExcerpt = showArabic
    ? excerptText(card.matn, perNarrativeBudget)
    : { value: "", truncated: false };
  const englishExcerpt =
    showEnglish && card.english
      ? excerptText(card.english.matn, perNarrativeBudget)
      : { value: null, truncated: false };
  const englishIsnadExcerpt =
    englishLeads && card.english?.isnad
      ? excerptText(card.english.isnad, 60)
      : { value: card.english?.isnad ?? null, truncated: false };
  const isnadExcerpt = showArabic
    ? excerptRuns(card.isnadRuns, 72)
    : { value: [], truncated: false };

  // ---- composition, measured before anything is painted ---------------------
  interface Draft {
    matn: string;
    english: string | null;
    englishIsnad: string | null;
  }

  const buildBlocks = (draft: Draft, matnSize: number, englishSize: number): Block[] => {
    const blocks: Block[] = [];

    if (showArabic && isnadExcerpt.value.length) {
      // The chain is provenance and sets small; the Imam it arrives at is the
      // speaker and comes back up to reading size.
      const runs: Run[] = isnadExcerpt.value.map((run) => ({
        text: run.text,
        font: arabic(run.emphasis ? 38 : 25),
        color: run.emphasis ? theme.accent : theme.muted,
      }));
      blocks.push({
        lines: layoutRuns(measure, runs, contentW, 1.62, RTL),
        direction: RTL,
        justify: false,
        spaceBefore: 34,
      });
    }

    if (showArabic) {
      blocks.push({
        lines: layoutRuns(
          measure,
          [{ text: draft.matn, font: arabic(matnSize), color: theme.ink }],
          contentW,
          1.95,
          RTL
        ),
        direction: RTL,
        justify: true,
        spaceBefore: 30,
        // The one ornamental moment inside the panel, and it marks a real
        // boundary: provenance above it, the narration below.
        rule: isnadExcerpt.value.length ? "rosette" : undefined,
      });
    }

    if (showEnglish && draft.english) {
      if (englishLeads && draft.englishIsnad) {
        blocks.push({
          lines: layoutRuns(
            measure,
            [{ text: draft.englishIsnad, font: sans(24), color: theme.muted }],
            contentW,
            1.6,
            LTR
          ),
          direction: LTR,
          justify: false,
          spaceBefore: 34,
        });
      }
      blocks.push({
        lines: layoutRuns(
          measure,
          [
            {
              text: draft.english,
              font: englishLeads ? serif(englishSize) : sans(englishSize),
              color: englishLeads ? theme.ink : theme.muted,
            },
          ],
          contentW,
          englishLeads ? 1.55 : 1.62,
          LTR
        ),
        direction: LTR,
        justify: false,
        spaceBefore: showArabic ? 30 : 34,
        rule: showArabic ? "hairline" : undefined,
      });
    }
    return blocks;
  };

  const headerH = 59;
  const footerH = 78;
  const bodyTop = cardY + PAD_Y + headerH;
  const footerTop = cardY + cardH - PAD_Y - footerH;
  const available = footerTop - bodyTop - 24;

  const fullDraft: Draft = {
    matn: matnExcerpt.value,
    english: englishExcerpt.value,
    englishIsnad: englishIsnadExcerpt.value,
  };
  const initiallyTruncated =
    matnExcerpt.truncated ||
    englishExcerpt.truncated ||
    englishIsnadExcerpt.truncated ||
    isnadExcerpt.truncated;

  // Fit by measurement: the largest type that still clears the footer. A short
  // narration is set large and fills the folio; a long one steps down. Both
  // scales move together on one parameter so Arabic and English keep relation.
  // Story carries 570px more frame than portrait, so it can hold a slightly
  // larger size. Only slightly: a manuscript keeps its text size steady and
  // lets the page carry the difference, and type scaled up to fill the frame
  // stops reading as set and starts reading as a poster.
  const arabicMax = spec.height >= 1900 ? 66 : ARABIC_MAX;
  const scaled = (t: number) => ({
    matn: Math.round(ARABIC_MIN + (arabicMax - ARABIC_MIN) * t),
    english: englishLeads
      ? Math.round(ENGLISH_LEAD_MIN + (ENGLISH_LEAD_MAX - ENGLISH_LEAD_MIN) * t)
      : Math.round(ENGLISH_SUB_MIN + (ENGLISH_SUB_MAX - ENGLISH_SUB_MIN) * t),
  });
  const fitsAt = (draft: Draft, t: number): Block[] | null => {
    const { matn, english } = scaled(t);
    const built = buildBlocks(draft, matn, english);
    return blocksHeight(built) <= available ? built : null;
  };

  let blocks = fitsAt(fullDraft, 1);
  if (!blocks) {
    let low = 0;
    let high = 1;
    for (let i = 0; i < 5; i += 1) {
      const mid = (low + high) / 2;
      const candidate = fitsAt(fullDraft, mid);
      if (candidate) {
        blocks = candidate;
        low = mid;
      } else {
        high = mid;
      }
    }
    // The search brackets t but never evaluates its floor, so a narration that
    // only fits at the smallest legible size would otherwise be cut for no
    // reason. Test the floor before giving up on setting it whole.
    if (!blocks) blocks = fitsAt(fullDraft, 0);
  }

  // Below the legibility floor the honest move is to set the opening and let
  // the permalink carry the rest, not to shrink scripture into noise.
  let truncated = initiallyTruncated;
  if (!blocks) {
    truncated = true;
    const trim = (text: string, keep: number): string => {
      const words = text.split(/\s+/);
      return words.length <= keep ? text : `${words.slice(0, keep).join(" ")} …`;
    };
    const largestDraft = Math.max(
      fullDraft.matn.split(/\s+/).length,
      fullDraft.english?.split(/\s+/).length ?? 0
    );
    let low = 10;
    let high = Math.min(240, largestDraft);
    while (low <= high) {
      const keep = Math.floor((low + high) / 2);
      const candidate = fitsAt(
        {
          matn: trim(fullDraft.matn, keep),
          english: fullDraft.english ? trim(fullDraft.english, keep) : null,
          englishIsnad: fullDraft.englishIsnad,
        },
        0
      );
      if (candidate) {
        blocks = candidate;
        low = keep + 1;
      } else {
        high = keep - 1;
      }
    }
  }
  const composition = blocks ?? [];

  // ---- paint ---------------------------------------------------------------
  ctx.fillStyle = theme.background;
  ctx.fillRect(0, 0, spec.width, spec.height);

  // The ground the folio sits on. A dark surface swallows fine line work, so
  // it gets a little more of it than a light one.
  const darkGround = isDark(theme.background);
  drawGirihField(
    ctx,
    { x: 0, y: 0, width: spec.width, height: spec.height },
    {
      color: darkGround ? theme.accent : theme.bronze,
      alpha: darkGround ? 0.11 : 0.085,
      cell: 104,
      lineWidth: 1.4,
    }
  );
  drawGrain(ctx, { x: 0, y: 0, width: spec.width, height: spec.height }, 0.05);

  ctx.fillStyle = theme.shadow;
  ctx.fillRect(cardX + SHADOW, cardY + SHADOW, cardW, cardH);
  ctx.fillStyle = theme.surface;
  ctx.fillRect(cardX, cardY, cardW, cardH);
  drawGrain(ctx, { x: cardX, y: cardY, width: cardW, height: cardH }, 0.035);
  drawManuscriptFrame(
    ctx,
    { x: cardX, y: cardY, width: cardW, height: cardH },
    { line: theme.line, accent: theme.bronze }
  );
  drawCornerPieces(ctx, { x: cardX, y: cardY, width: cardW, height: cardH }, theme.bronze);

  let y = cardY + PAD_Y;
  if (card.bookTitle) {
    ctx.direction = RTL;
    ctx.textAlign = "right";
    ctx.font = fontString(arabic(40));
    ctx.fillStyle = theme.ink;
    ctx.fillText(card.bookTitle, contentX + contentW, y + 34);
  }
  ctx.direction = LTR;
  ctx.textAlign = "left";
  ctx.font = fontString(sans(23, 600));
  ctx.fillStyle = theme.bronze;
  ctx.fillText(
    [card.location, card.printedNumber ? `no. ${card.printedNumber}` : null]
      .filter(Boolean)
      .join("  ·  "),
    contentX,
    y + 30
  );
  y += headerH - 1;

  drawRule(ctx, contentX, y, contentW, theme.line);
  // Bronze marks bibliography: a short weighted segment at the RTL reading
  // edge, so the rule reads as part of the citation, not as a plain divider.
  ctx.save();
  ctx.strokeStyle = theme.bronze;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(contentX + contentW - 104, y + 0.5);
  ctx.lineTo(contentX + contentW, y + 0.5);
  ctx.stroke();
  ctx.restore();
  y += 1;

  // Spread whatever room is left over: a lead-in under the header, a share
  // between the blocks, and the remainder above the footer. Dumping it all in
  // one place is what leaves a tall frame looking half-empty.
  const slack = Math.max(0, available - blocksHeight(composition));
  const gaps = Math.max(0, composition.length - 1);
  // Blocks get a modest extra breath, capped — spreading them by a share of the
  // slack pulls a short narration apart instead of letting it read as one
  // composed group. Whatever is left centres the group optically, a little
  // above true centre, which is what stops a tall frame looking top-weighted.
  const spread = Math.min(slack * 0.25, 26 * gaps);
  const betweenBlocks = gaps > 0 ? spread / gaps : 0;
  y += (slack - spread) * 0.45;

  composition.forEach((block, index) => {
    y += block.spaceBefore + (index > 0 ? betweenBlocks : 0);
    if (block.rule === "rosette") {
      drawRosetteDivider(ctx, contentX, y + ROSETTE_GAP / 2, contentW, {
        line: theme.line,
        accent: theme.bronze,
      });
      y += ROSETTE_GAP;
    } else if (block.rule) {
      drawRule(ctx, contentX, y, contentW, theme.line);
      y += RULE_GAP;
    }
    y += drawLines(ctx, measure, block.lines, {
      left: contentX,
      top: y,
      width: contentW,
      direction: block.direction,
      justify: block.justify,
    });
  });

  drawRule(ctx, contentX, footerTop, contentW, theme.line);
  const footerY = footerTop + 30;

  ctx.direction = LTR;
  ctx.textAlign = "right";
  ctx.font = fontString(sans(23, 600));
  ctx.fillStyle = theme.ink;
  ctx.fillText("usul16.com", contentX + contentW, footerY + 8);
  ctx.font = fontString(sans(21));
  ctx.fillStyle = theme.muted;
  ctx.fillText(card.publicId, contentX + contentW, footerY + 40);
  const rightBlock = Math.max(
    measure(sans(23, 600), "usul16.com").advance,
    measure(sans(21), card.publicId).advance
  );

  // Where a seal used to sit. A tick beside the words "verified source" reads
  // as a verdict on the narration — and this project grades nothing here, on a
  // corpus where al-Majlisi calls plenty of these reports weak. What is
  // actually verified is the page, which the header and permalink already
  // carry, so the space goes to the chapter the report sits in: real context,
  // shown nowhere else on the image, and no claim about its authenticity.
  drawStarMark(ctx, contentX + 9, footerY + 15, 9, theme.bronze);
  const labelFont = sans(22, 600);
  const labelX = contentX + 30;
  const labelRoom = contentW - (labelX - contentX) - rightBlock - 40;
  ctx.textAlign = "left";
  if (card.chapter) {
    ctx.font = fontString(labelFont);
    ctx.fillStyle = theme.muted;
    ctx.fillText(ellipsize(measure, labelFont, card.chapter, labelRoom), labelX, footerY + 22);
  }
  if (truncated) {
    // An ellipsis alone is a weak thing to hang an abridgement of scripture on.
    const usedWidth = card.chapter
      ? measure(labelFont, ellipsize(measure, labelFont, card.chapter, labelRoom)).advance + 14
      : 0;
    ctx.font = fontString(sans(21));
    ctx.fillStyle = theme.bronze;
    ctx.fillText(card.chapter ? "· excerpt" : "excerpt", labelX + usedWidth, footerY + 22);
  }

  return { canvas, truncated };
}

export function canvasToBlob(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    // A second synchronous encode makes a genuinely slow phone do the same
    // expensive job twice. Give the standards-based encoder a firm deadline
    // and return control to the reader if that browser cannot finish it.
    const timeoutId = window.setTimeout(
      () => reject(new Error("Image encoding timed out")),
      4_500
    );
    canvas.toBlob((blob) => {
      window.clearTimeout(timeoutId);
      if (blob) resolve(blob);
      else reject(new Error("Could not encode the image"));
    }, "image/png");
  });
}

export function shareFileName(card: ShareCard, format: ShareFormat): string {
  return `usul16-${card.publicId.replace(/[^a-z0-9-]+/gi, "-")}-${format}.png`;
}
