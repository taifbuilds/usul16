// The content model behind every share surface: clipboard text and the
// rendered image both read from this, so what a reader copies and what they
// post can never drift apart.

import type { HadithRead } from "@/lib/api/types";
import { formatArabicText, formatArabicTitle } from "@/lib/arabic";
import { formatCitation } from "@/lib/citation";
import { toWesternDigits } from "@/lib/inline";
import { isPublicHumanTranslation } from "@/lib/translationPublication";
import { splitIsnadAtImam, type IsnadRun } from "@/lib/share/imam";

// Printed footnote references only mean something beside the footnotes they
// point at. Neither the clipboard nor the image carries those, so a bare "[٤]"
// left in the text would read as part of the narration.
const FOOTNOTE_MARKER_RE = /\[\s*[0-9٠-٩]+\s*\]/g;

function withoutFootnoteMarkers(text: string): string {
  return text.replace(FOOTNOTE_MARKER_RE, "").replace(/\s{2,}/g, " ").trim();
}

/** Which text the reader chose to share. */
export type ShareLanguage = "ar" | "both" | "en";

export const SHARE_LANGUAGES: { value: ShareLanguage; label: string; short: string }[] = [
  { value: "ar", label: "Arabic", short: "ع" },
  { value: "both", label: "Arabic + English", short: "ع/EN" },
  { value: "en", label: "English", short: "EN" },
];

export interface ShareCard {
  publicId: string;
  /** Arabic title of the collection, as printed. */
  bookTitle: string | null;
  /** "vol. 1 · p. 42" — the printed location, never a database id. */
  location: string;
  printedNumber: string | null;
  chapter: string | null;
  isnadRuns: IsnadRun[];
  matn: string;
  /** Present only when a publishable human translation exists. */
  english: { matn: string; isnad: string | null; translator: string | null } | null;
  url: string;
  citation: string;
}

function translatorCredit(provenance: Record<string, unknown> | null): string | null {
  const translator = provenance?.translator;
  return typeof translator === "string" && translator.trim() ? translator.trim() : null;
}

function locationLabel(hadith: HadithRead): string {
  const pages =
    hadith.page_end !== hadith.page_start
      ? `pp. ${hadith.page_start}–${hadith.page_end}`
      : `p. ${hadith.page_start}`;
  return [hadith.volume_start !== null ? `vol. ${hadith.volume_start}` : null, pages]
    .filter(Boolean)
    .join(" · ");
}

export function buildShareCard(
  hadith: HadithRead,
  bookTitle: string | null,
  origin: string
): ShareCard {
  const url = `${origin}/hadith/${encodeURIComponent(hadith.public_id)}`;
  const title = bookTitle ? formatArabicTitle(bookTitle) : null;
  // The publication gate is the same one the reader uses: an unattributed or
  // AI-tier translation is never quietly baked into an image that will travel
  // without this page around it.
  const translation = isPublicHumanTranslation(hadith.translation) ? hadith.translation : null;
  const chapter =
    hadith.structure?.mapping_status === "matched"
      ? hadith.structure.chapter_name_en || hadith.structure.kitab_name_en || null
      : null;

  return {
    publicId: hadith.public_id,
    bookTitle: title,
    location: locationLabel(hadith),
    // The header sets volume and page in Latin numerals, so the printed number
    // has to join them rather than sit beside them in Arabic-Indic digits.
    printedNumber: hadith.printed_number ? toWesternDigits(hadith.printed_number) : null,
    chapter,
    isnadRuns: hadith.isnad_raw
      ? splitIsnadAtImam(withoutFootnoteMarkers(formatArabicText(hadith.isnad_raw)))
      : [],
    matn: withoutFootnoteMarkers(formatArabicText(hadith.matn_raw)),
    english: translation
      ? {
          matn: translation.matn_translation.trim(),
          isnad: translation.rendered_isnad_en?.trim() || null,
          translator: translatorCredit(translation.provenance_json),
        }
      : null,
    url,
    citation: formatCitation({
      title: title ?? "Shia hadith",
      volumeNumber: hadith.volume_start,
      pageNumber: hadith.page_start,
      pageEnd: hadith.page_end,
      printedNumber: hadith.printed_number,
      publicId: hadith.public_id,
      canonicalUrl: url,
      sourceUrl: hadith.source_url,
    }),
  };
}

/** Languages this hadith can actually be shared in right now. */
export function availableLanguages(card: ShareCard): ShareLanguage[] {
  return card.english ? ["ar", "both", "en"] : ["ar"];
}

/** Plain text for the clipboard: the narration, then where it comes from. */
export function shareText(card: ShareCard, language: ShareLanguage): string {
  const blocks: string[] = [];
  const isnad = card.isnadRuns.map((run) => run.text).join(" ");

  if (language !== "en") {
    blocks.push([isnad, card.matn].filter(Boolean).join("\n"));
  }
  if (language !== "ar" && card.english) {
    const credit = card.english.translator ? ` — tr. ${card.english.translator}` : "";
    blocks.push(
      [card.english.isnad, `${card.english.matn}${credit}`].filter(Boolean).join("\n")
    );
  }
  blocks.push(card.citation);
  return blocks.join("\n\n");
}
