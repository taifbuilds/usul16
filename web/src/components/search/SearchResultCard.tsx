import Link from "next/link";
import { formatArabicText, formatArabicTitle } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import type { SearchResult } from "@/lib/api/types";
import { Citation } from "@/components/citation/Citation";

export function SearchResultCard({ result }: { result: SearchResult }) {
  const { book, page, snippet } = result;
  const href = `/read/${book.id}/${page.volume_number ?? 1}/${page.page_number}`;
  const title = formatArabicTitle(book.title_original);

  return (
    <div className="rounded-2xl border border-border bg-surface p-5 hover:border-accent">
      <Link href={href} className="block">
        <p dir="rtl" lang="ar" className={`${amiri.className} text-right text-base font-medium text-accent`}>
          {title}
        </p>
        {/* snippet is built from text_normalised (diacritic-stripped) by the
            backend, so it won't look pixel-identical to the verbatim text_raw
            shown in the reader — known v1 limitation, see plan. */}
        <p dir="rtl" lang="ar" className={`${amiri.className} mt-2 text-right text-lg leading-relaxed`}>
          {formatArabicText(snippet)}
        </p>
      </Link>
      <div className="mt-3 border-t border-border pt-3">
        <Citation
          title={title}
          volumeNumber={page.volume_number}
          pageNumber={page.page_number}
          sourceUrl={page.source_url}
        />
      </div>
    </div>
  );
}
