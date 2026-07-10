import Link from "next/link";
import { amiri } from "@/lib/fonts";
import { formatArabicTitle } from "@/lib/arabic";
import type { BookSummary } from "@/lib/api/types";
import { ContentBadge } from "@/components/books/ContentBadge";

export function BookCard({ book, index }: { book: BookSummary; index?: number }) {
  const title = formatArabicTitle(book.title_original);
  const author = book.authors?.[0];

  return (
    <Link
      href={`/books/${book.id}`}
      className="group flex flex-col justify-between rounded-2xl border border-border bg-surface p-6 transition hover:border-accent hover:shadow-sm"
    >
      <div>
        {index !== undefined ? (
          <p className="text-xs font-semibold tracking-[0.2em] text-muted uppercase">
            {String(index).padStart(2, "0")} · Kitāb
          </p>
        ) : null}

        <p dir="rtl" lang="ar" className={`${amiri.className} mt-3 text-right text-2xl leading-snug text-accent`}>
          {title}
        </p>

        <div className="mt-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 text-sm text-muted">
          {author ? (
            <span dir="rtl" lang="ar" className={amiri.className}>
              {formatArabicTitle(author.name_original)}
            </span>
          ) : (
            <span />
          )}
          {book.volume_count ? <span>{book.volume_count} vol.</span> : null}
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between border-t border-border pt-4">
        <ContentBadge hasContent={book.has_content} />
        <span className="text-sm font-medium text-accent group-hover:underline">Open →</span>
      </div>
    </Link>
  );
}
