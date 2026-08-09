"use client";

import { useCallback, useState } from "react";
import type {
  HadithCommentaryRead,
  HadithCommentarySummaryRead,
  HadithTranslationRead,
} from "@/lib/api/types";
import { getHadithCommentaries } from "@/lib/api/books";
import { formatArabicText } from "@/lib/arabic";
import { DisclosureChevron } from "@/components/ui/DisclosureChevron";

// Translation, commentary and footnotes are reading layers, not rival cards.
// Keep one unmistakable control for each layer. A single commentary disclosure
// then lets the reader choose its source, instead of making several nearly
// identical sharh panels compete for attention below the hadith.

/** Credit the people who actually made the translation — the translator or the
 * publishing edition (e.g. "Bab Ul Qaim Publications") — never the aggregator
 * site a copy happened to be collected from. */
function translationSourceLabel(translation: HadithTranslationRead): string | null {
  const provenance = translation.provenance_json;
  const translator =
    typeof provenance?.translator === "string" && provenance.translator.trim()
      ? provenance.translator.trim()
      : null;
  if (translator) return prettifySourceName(translator);
  const edition = translation.model?.trim();
  if (edition) return prettifySourceName(edition);
  const provider = translation.provider?.trim();
  return provider ? prettifySourceName(provider) : null;
}

const AGGREGATOR_NAME_RE = /thaqalayn/i;

function prettifySourceName(raw: string): string | null {
  if (AGGREGATOR_NAME_RE.test(raw)) return null;
  const words = raw.replace(/[-_]+/g, " ").trim().split(/\s+/);
  return words.map((w) => (w.length <= 2 ? w : w[0].toUpperCase() + w.slice(1))).join(" ") || null;
}

function translationSourceUrl(translation: HadithTranslationRead): string | null {
  const usable = (value: unknown): string | null =>
    typeof value === "string" && value.startsWith("https://") ? value : null;
  const provenance = translation.provenance_json;
  const directUrl = usable(provenance?.source_url);
  if (directUrl) return directUrl;
  const sourceEvidence = provenance?.source_evidence;
  if (typeof sourceEvidence !== "object" || sourceEvidence === null) return null;
  const pdf = (sourceEvidence as Record<string, unknown>).pdf;
  if (typeof pdf !== "object" || pdf === null) return null;
  return usable((pdf as Record<string, unknown>).source_url);
}

function sourceLinkLabel(url: string): string {
  return AGGREGATOR_NAME_RE.test(url) ? "Thaqalayn link" : "Source";
}

function printedLocation(summary: HadithCommentarySummaryRead): string {
  const sameVolume = summary.volume_start === summary.volume_end;
  const samePage = summary.page_start === summary.page_end;
  if (sameVolume && samePage) return `ج ${summary.volume_start} · ص ${summary.page_start}`;
  return `ج ${summary.volume_start}–${summary.volume_end} · ص ${summary.page_start}–${summary.page_end}`;
}

/** Holds the space the passage will fill, so opening doesn't shift the page. */
function TextSkeleton() {
  return (
    <div aria-hidden="true" className="space-y-3 py-1">
      {["100%", "96%", "62%"].map((width) => (
        <div key={width} style={{ width }} className="shimmer h-4 rounded-full bg-foreground/10" />
      ))}
    </div>
  );
}

export function ApparatusShelf({
  publicId,
  commentaries,
  translation,
}: {
  publicId: string;
  commentaries: HadithCommentarySummaryRead[];
  translation: HadithTranslationRead | null;
}) {
  const [loaded, setLoaded] = useState<HadithCommentaryRead[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSourceKey, setSelectedSourceKey] = useState(() => commentaries[0]?.source_key ?? "");

  // Fetched once on the first hint of interest, so opening a row is instant.
  const load = useCallback(
    (retry = false) => {
      if (!commentaries.length) return;
      if (loading || (loaded && !retry)) return;
      setLoading(true);
      setError(null);
      getHadithCommentaries(publicId)
        .then((items) => setLoaded(items ?? []))
        .catch(() => setError("تعذر تحميل الشرح."))
        .finally(() => setLoading(false));
    },
    [commentaries.length, loaded, loading, publicId]
  );

  if (!commentaries.length && !translation) return null;

  const selectedSummary =
    commentaries.find((item) => item.source_key === selectedSourceKey) ?? commentaries[0] ?? null;
  const selectedCommentary = selectedSummary
    ? loaded?.find((item) => item.source_key === selectedSummary.source_key) ?? null
    : null;

  return (
    <section className="mt-7 divide-y divide-border border-y border-border" aria-label="Reading layers">
      {translation ? <TranslationDisclosure translation={translation} /> : null}

      {selectedSummary ? (
        <CommentaryDisclosure
          summaries={commentaries}
          selectedSummary={selectedSummary}
          selectedSourceKey={selectedSummary.source_key}
          onSourceChange={setSelectedSourceKey}
          commentary={selectedCommentary}
          loading={loading}
          error={error}
          onOpen={() => load()}
          onRetry={() => load(true)}
        />
      ) : null}
    </section>
  );
}

function CommentaryDisclosure({
  summaries,
  selectedSummary,
  selectedSourceKey,
  onSourceChange,
  commentary,
  loading,
  error,
  onOpen,
  onRetry,
}: {
  summaries: HadithCommentarySummaryRead[];
  selectedSummary: HadithCommentarySummaryRead;
  selectedSourceKey: string;
  onSourceChange: (sourceKey: string) => void;
  commentary: HadithCommentaryRead | null;
  loading: boolean;
  error: string | null;
  onOpen: () => void;
  onRetry: () => void;
}) {
  const text = commentary ? formatArabicText(commentary.commentary_raw) : "";
  const lead = commentary?.source_label?.trim() ?? "";
  const hasLead = Boolean(lead) && text.startsWith(lead);

  return (
    <details
      className="group"
      onToggle={(event) => {
        if (event.currentTarget.open) onOpen();
      }}
    >
      <summary
        dir="ltr"
        lang="en"
        onPointerEnter={onOpen}
        onFocus={onOpen}
        className="flex min-h-14 cursor-pointer list-none items-center justify-between gap-4 px-1 py-2 transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent/35"
      >
        <span className="flex min-w-0 items-center gap-3">
          <span
            aria-hidden="true"
            className="grid size-8 shrink-0 place-items-center rounded-sm bg-accent text-base font-semibold text-accent-foreground"
          >
            ش
          </span>
          <span className="min-w-0 text-left">
            <span className="block text-sm font-semibold text-foreground">Commentary</span>
            <span className="block text-xs text-muted">
              {summaries.length} available source{summaries.length === 1 ? "" : "s"}
            </span>
          </span>
        </span>
        <DisclosureChevron className="me-2 text-muted motion-safe:transition-transform motion-safe:duration-200 group-open:rotate-180" />
      </summary>

      <div className="border-t border-border pb-5 pt-5 sm:ps-11">
        <label
          className="block max-w-xl text-xs font-semibold text-muted"
          htmlFor={`commentary-source-${selectedSummary.source_key}`}
        >
          Choose commentary
          <select
            id={`commentary-source-${selectedSummary.source_key}`}
            dir="rtl"
            value={selectedSourceKey}
            onChange={(event) => onSourceChange(event.target.value)}
            className="mt-2 block min-h-11 w-full rounded-md border border-border-strong bg-surface px-3 text-right text-sm font-medium text-foreground transition-colors hover:border-accent focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25"
          >
            {summaries.map((summary) => (
              <option key={summary.source_key} value={summary.source_key}>
                {summary.label_ar || summary.title_ar} — {summary.author_ar}
              </option>
            ))}
          </select>
        </label>

        {selectedSummary.evidence === "position" ? (
          // Never let a positional placement pass for a quoted one.
          <p dir="rtl" lang="ar" className="mt-4 text-xs leading-relaxed text-muted">
            الشارح لم يُعِد نصّ الحديث هنا؛ رُبط الشرح بترتيبه داخل الباب.
          </p>
        ) : null}

        {loading ? <div className="mt-5"><TextSkeleton /></div> : null}

        {error ? (
          <div role="alert" className="mt-5 flex flex-wrap items-center gap-x-3 gap-y-1">
            <p className="text-sm text-foreground/80">{error}</p>
            <button
              type="button"
              onClick={onRetry}
              className="min-h-9 rounded-md border border-border px-3 text-sm text-accent transition-colors hover:border-accent"
            >
              إعادة المحاولة
            </button>
          </div>
        ) : null}

        {!loading && !error && !commentary ? (
          <p className="mt-5 text-sm text-muted">لا يوجد شرح متاح لهذا الحديث.</p>
        ) : null}

        {!loading && commentary ? (
          <>
            <p dir="rtl" lang="ar" className="reader-sharh mt-5 whitespace-pre-line text-justify text-foreground/90">
              {hasLead ? (
                <>
                  <span className="font-medium text-gold">{lead}</span>
                  {text.slice(lead.length)}
                </>
              ) : (
                text
              )}
            </p>
            <p className="mt-3 text-xs text-muted">{printedLocation(selectedSummary)}</p>
          </>
        ) : null}
      </div>
    </details>
  );
}

function TranslationDisclosure({ translation }: { translation: HadithTranslationRead }) {
  const source = translationSourceLabel(translation);
  const url = translationSourceUrl(translation);

  return (
    <details dir="ltr" lang="en" className="group text-left">
      <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between gap-4 px-1 py-2 transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent/35">
        <span className="flex min-w-0 items-center gap-3">
          <span
            aria-hidden="true"
            className="grid size-8 shrink-0 place-items-center rounded-sm border border-gold/55 text-[0.68rem] font-bold text-gold"
          >
            EN
          </span>
          <span className="min-w-0 text-left">
            <span className="block text-sm font-semibold text-foreground">English translation</span>
            {source ? <span className="block truncate text-xs text-muted">{source}</span> : null}
          </span>
        </span>
        <DisclosureChevron className="me-2 text-muted motion-safe:transition-transform motion-safe:duration-200 group-open:rotate-180" />
      </summary>

      <div className="border-t border-border pb-5 pt-5 sm:ps-11">
        {translation.full_translation ? (
          // Verbatim external text: the numbered English isnad and matn are one
          // continuous block, exactly as the source publishes it.
          <p className="whitespace-pre-line text-base leading-8 text-foreground/90 sm:text-lg">
            {translation.full_translation}
          </p>
        ) : (
          <>
            {translation.rendered_isnad_en ? (
              <p className="mb-4 border-b border-dashed border-border pb-4 text-sm leading-relaxed text-muted">
                <span className="font-medium text-foreground/70">Chain: </span>
                {translation.rendered_isnad_en}
              </p>
            ) : null}
            <p className="text-base leading-8 text-foreground/90 sm:text-lg">
              {translation.matn_translation}
            </p>
          </>
        )}
        <p className="mt-4 text-xs leading-relaxed text-muted">
          {source ? (
            <>
              Translation: <span>{source}</span>
              <span className="mx-1 text-border">&middot;</span>
            </>
          ) : null}
          {url ? (
            <>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:underline"
              >
                {sourceLinkLabel(url)}
              </a>
              <span className="mx-1 text-border">&middot;</span>
            </>
          ) : null}
          The Arabic above is the original.
        </p>
      </div>
    </details>
  );
}
