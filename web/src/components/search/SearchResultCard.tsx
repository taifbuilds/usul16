import Link from "next/link";
import { formatArabicText, formatArabicTitle } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import type { SearchResult } from "@/lib/api/types";
import { hasPublicHumanSourceEvidence } from "@/lib/translationPublication";
import { Citation } from "@/components/citation/Citation";

export function SearchResultCard({ result }: { result: SearchResult }) {
  const { book, page, snippet } = result;
  const isEnglish = result.match_type === "english";
  if (isEnglish && !hasPublicHumanSourceEvidence(result.translation_evidence)) return null;
  const href = result.hadith_public_id
    ? `/hadith/${encodeURIComponent(result.hadith_public_id)}`
    : `/read/${book.id}/${page.volume_number ?? 1}/${page.page_number}`;
  const title = formatArabicTitle(book.title_original);

  return (
    <article className="group relative px-1 py-7 transition-colors hover:bg-surface-2 sm:px-5">
      <Link href={href} className="relative block focus-visible:outline-offset-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p dir="rtl" lang="ar" className={`${amiri.className} text-right text-lg font-medium text-accent`}>{title}</p>
          <span className="flex min-h-11 items-center gap-2 text-xs font-semibold text-muted transition-colors group-hover:text-accent">
            {isEnglish ? "English translation" : result.match_type === "book" ? "Book title" : "Arabic source"}
            <span aria-hidden="true">→</span>
          </span>
        </div>
        {/* snippet is built from text_normalised (diacritic-stripped) by the
            backend, so it won't look pixel-identical to the verbatim text_raw
            shown in the reader — known v1 limitation, see plan. */}
        {isEnglish ? (
          <p lang="en" className="mt-3 max-w-[72ch] text-base leading-7 text-foreground/90">
            {snippet}
          </p>
        ) : (
          <p dir="rtl" lang="ar" className={`${amiri.className} mt-3 text-right text-xl leading-[2] text-foreground/90`}>
            {formatArabicText(snippet)}
          </p>
        )}
      </Link>
      <div className="relative mt-4 border-t border-border pt-3 transition-colors group-hover:border-accent">
        <Citation
          title={title}
          volumeNumber={page.volume_number}
          pageNumber={page.page_number}
          sourceUrl={page.source_url}
          printedNumber={result.hadith_printed_number}
          publicId={result.hadith_public_id}
          permanentPath={href}
        />
      </div>
    </article>
  );
}
