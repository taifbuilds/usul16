import Link from "next/link";
import { getBooks } from "@/lib/api/books";
import { amiri } from "@/lib/fonts";
import { BookCard } from "@/components/books/BookCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";
import type { Metadata } from "next";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { getLocale } from "@/lib/i18n/locale";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const t = getDictionary(await getLocale());
  return { title: t.books.eyebrow, description: t.books.lead, alternates: { canonical: "/books" } };
}

const LIMIT = 50;

export default async function BooksPage({
  searchParams,
}: {
  searchParams: Promise<{ view?: string; skip?: string }>;
}) {
  const [params, locale] = await Promise.all([searchParams, getLocale()]);
  const t = getDictionary(locale);
  const view = params.view === "all" ? "all" : "available";
  const skip = Number(params.skip ?? 0) || 0;
  const books = await getBooks({ skip, limit: LIMIT, hasContent: view === "available" ? true : undefined });
  const priority = ["11005", "11021", "10083", "11002", "71860", "11025", "14036"];
  const orderedBooks = [...books].sort((left, right) => {
    const leftRank = priority.indexOf(left.source_book_id);
    const rightRank = priority.indexOf(right.source_book_id);
    return (leftRank < 0 ? priority.length : leftRank) - (rightRank < 0 ? priority.length : rightRank);
  });

  return (
    <div className="library-stage min-h-screen border-b border-border">
      <header className="border-b border-[color:var(--stage-line)]">
        <div className="mx-auto grid max-w-[90rem] gap-6 px-4 py-10 sm:px-6 sm:py-14 lg:grid-cols-[1fr_auto] lg:items-end lg:px-8">
          <div>
            <div className="flex items-center gap-3 text-sm font-semibold text-[color:var(--stage-accent)]"><span className="h-px w-9 bg-current" />{t.books.eyebrow}</div>
            <h1 className="mt-4 font-serif text-4xl font-semibold leading-tight text-[color:var(--stage-ink)] sm:text-6xl">{t.books.title}</h1>
            <p className="mt-5 max-w-2xl text-base leading-8 text-[color:var(--stage-muted)]">
              {t.books.lead}
            </p>
          </div>
          <p dir="rtl" lang="ar" className={`${amiri.className} max-w-full text-right text-4xl text-[color:var(--stage-gold)] sm:text-5xl`}>{t.books.arabicTitle}</p>
        </div>
      </header>

      <div className="mx-auto max-w-[90rem] px-4 pb-24 sm:px-6 lg:px-8">
      <div className="flex flex-col items-start gap-4 border-b border-[color:var(--stage-line)] py-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2 text-sm" aria-label={t.books.catalogueView}>
        <Link
          href="/books"
          className={`rounded-md px-4 py-2.5 font-medium transition-colors ${
            view === "available" ? "bg-[color:var(--stage-accent)] text-[color:var(--stage-accent-foreground)]" : "border border-[color:var(--stage-line-strong)] text-[color:var(--stage-muted)] hover:border-[color:var(--stage-accent)] hover:text-[color:var(--stage-accent)]"
          }`}
        >
          {t.books.availableToRead}
        </Link>
        <Link
          href="/books?view=all"
          className={`rounded-md px-4 py-2.5 font-medium transition-colors ${
            view === "all" ? "bg-[color:var(--stage-accent)] text-[color:var(--stage-accent-foreground)]" : "border border-[color:var(--stage-line-strong)] text-[color:var(--stage-muted)] hover:border-[color:var(--stage-accent)] hover:text-[color:var(--stage-accent)]"
          }`}
        >
          {t.books.completeCatalogue}
        </Link>
        </div>
        <p className="max-w-full text-xs font-medium text-[color:var(--stage-muted)]">{books.length} {t.books.worksShown}</p>
      </div>

      <div className="mt-7 flex flex-wrap items-center justify-between gap-3 border-b border-[color:var(--stage-line)] pb-7 text-sm text-[color:var(--stage-muted)]">
        <p>{t.books.stagesNote}</p>
        <Link href="/methodology" className="inline-flex min-h-11 items-center font-semibold text-[color:var(--stage-accent)] hover:underline">
          {t.books.seeStatus} <span aria-hidden className="ms-1 rtl:-scale-x-100">→</span>
        </Link>
      </div>

      {books.length > 0 ? (
        <div className="library-shelf mt-12 grid gap-x-8 gap-y-14 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {orderedBooks.map((book, index) => <BookCard key={book.id} book={book} index={skip + index + 1} />)}
        </div>
      ) : (
        <div className="mt-10">
          <EmptyState
            title="No books found"
            description={view === "available" ? "Nothing has been fully crawled yet." : "The catalogue appears to be empty."}
          />
        </div>
      )}

      <div className="mt-16 border-t border-[color:var(--stage-line)] pt-6">
        <Pagination
          basePath="/books"
          skip={skip}
          limit={LIMIT}
          hasMore={books.length === LIMIT}
          extraParams={view === "all" ? { view: "all" } : {}}
        />
      </div>
      </div>
    </div>
  );
}
