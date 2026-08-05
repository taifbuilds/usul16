"use client";

import { useCallback, useState } from "react";
import type {
  HadithCommentaryRead,
  HadithCommentarySummaryRead,
  HadithTranslationRead,
} from "@/lib/api/types";
import { getHadithCommentaries } from "@/lib/api/books";
import { formatArabicText } from "@/lib/arabic";

// Translation and commentaries each keep their own disclosure, so a reader can
// see at a glance everything that exists for this hadith without opening
// anything. The sharh rows are deliberately *not* boxed: a full bordered panel
// per commentary made the apparatus heavier than the report it explains, and
// the weight compounds with every commentary added. A hairline rule and a plain
// summary row carry the same structure at a fraction of the visual cost —
// matching the «الهوامش» row already at the foot of the card.

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

  return (
    <>
      {translation ? <TranslationDisclosure translation={translation} /> : null}

      {commentaries.map((summary) => (
        <SharhDisclosure
          key={summary.source_key}
          summary={summary}
          commentary={loaded?.find((item) => item.source_key === summary.source_key) ?? null}
          loading={loading}
          error={error}
          onOpen={() => load()}
          onRetry={() => load(true)}
        />
      ))}
    </>
  );
}

function SharhDisclosure({
  summary,
  commentary,
  loading,
  error,
  onOpen,
  onRetry,
}: {
  summary: HadithCommentarySummaryRead;
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
      className="group mt-4 border-t border-border pt-3"
      onToggle={(event) => {
        if (event.currentTarget.open) onOpen();
      }}
    >
      <summary
        onPointerEnter={onOpen}
        onFocus={onOpen}
        className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 text-sm"
      >
        <span className="flex min-w-0 flex-wrap items-baseline gap-x-2">
          <span className="font-medium text-gold">{summary.label_ar || summary.title_ar}</span>
          <span className="text-xs text-muted">{summary.author_ar}</span>
        </span>
        <span
          aria-hidden="true"
          className="shrink-0 text-muted motion-safe:transition-transform motion-safe:duration-200 group-open:rotate-180"
        >
          ⌄
        </span>
      </summary>

      <div className="mt-3">
        {summary.evidence === "position" ? (
          // Never let a positional placement pass for a quoted one.
          <p className="mb-3 text-xs leading-relaxed text-muted">
            الشارح لم يُعِد نصّ الحديث هنا؛ رُبط الشرح بترتيبه داخل الباب.
          </p>
        ) : null}

        {loading ? <TextSkeleton /> : null}

        {error ? (
          <div role="alert" className="flex flex-wrap items-center gap-x-3 gap-y-1">
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
          <p className="text-sm text-muted">لا يوجد شرح متاح لهذا الحديث.</p>
        ) : null}

        {!loading && commentary ? (
          <>
            <p className="reader-sharh whitespace-pre-line text-justify text-foreground/85">
              {hasLead ? (
                <>
                  <span className="font-medium text-gold">{lead}</span>
                  {text.slice(lead.length)}
                </>
              ) : (
                text
              )}
            </p>
            <p className="mt-3 text-xs text-muted">{printedLocation(summary)}</p>
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
    <details dir="ltr" lang="en" className="group mt-4 border-t border-border pt-3 text-left">
      <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 text-sm">
        <span className="flex min-w-0 flex-wrap items-baseline gap-x-2">
          <span className="font-medium text-accent">English translation</span>
          <span className="min-w-0 break-words text-xs text-muted">{source ?? ""}</span>
        </span>
        <span
          aria-hidden="true"
          className="shrink-0 text-muted motion-safe:transition-transform motion-safe:duration-200 group-open:rotate-180"
        >
          ⌄
        </span>
      </summary>

      <div className="mt-3">
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
