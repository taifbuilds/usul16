import Link from "next/link";
import { getBooks } from "@/lib/api/books";
import { amiri } from "@/lib/fonts";
import { BookCard } from "@/components/books/BookCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";
import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Hadith library",
  description: "Read the principal Shia hadith collections with direct routes to the represented printed sources.",
  alternates: { canonical: "/books" },
};

const LIMIT = 50;

export default async function BooksPage({
  searchParams,
}: {
  searchParams: Promise<{ view?: string; skip?: string }>;
}) {
  const params = await searchParams;
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
        <div className="mx-auto grid max-w-[90rem] gap-8 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[1fr_auto] lg:items-end lg:px-8">
          <div>
            <div className="flex items-center gap-3 text-sm font-semibold text-[color:var(--stage-accent)]"><span className="h-px w-9 bg-current" />The reading library</div>
            <h1 className="mt-5 font-serif text-5xl font-semibold leading-none tracking-[-0.025em] text-[color:var(--stage-ink)] sm:text-7xl">Choose a collection.</h1>
            <p className="mt-5 max-w-2xl text-base leading-8 text-[color:var(--stage-muted)]">
              Open a work as a book, then move through its chapters or follow the pagination of the printed edition. Every readable text keeps a direct source route.
            </p>
          </div>
          <p dir="rtl" lang="ar" className={`${amiri.className} text-5xl text-[color:var(--stage-gold)] sm:text-6xl`}>المكتبة</p>
        </div>
      </header>

      <div className="mx-auto max-w-[90rem] px-4 pb-24 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-center justify-between gap-5 border-b border-[color:var(--stage-line)] py-5">
        <div className="flex flex-wrap gap-2 text-sm" aria-label="Catalogue view">
        <Link
          href="/books"
          className={`rounded-md px-4 py-2.5 font-medium transition-colors ${
            view === "available" ? "bg-[color:var(--stage-accent)] text-[color:var(--stage-accent-foreground)]" : "border border-[color:var(--stage-line-strong)] text-[color:var(--stage-muted)] hover:border-[color:var(--stage-accent)] hover:text-[color:var(--stage-accent)]"
          }`}
        >
          Available to read
        </Link>
        <Link
          href="/books?view=all"
          className={`rounded-md px-4 py-2.5 font-medium transition-colors ${
            view === "all" ? "bg-[color:var(--stage-accent)] text-[color:var(--stage-accent-foreground)]" : "border border-[color:var(--stage-line-strong)] text-[color:var(--stage-muted)] hover:border-[color:var(--stage-accent)] hover:text-[color:var(--stage-accent)]"
          }`}
        >
          Complete catalogue
        </Link>
        </div>
        <p className="text-xs font-medium text-[color:var(--stage-muted)]">{books.length} works shown on this page</p>
      </div>

      <div className="mt-7 flex flex-wrap items-center justify-between gap-3 border-b border-[color:var(--stage-line)] pb-7 text-sm text-[color:var(--stage-muted)]">
        <p>Collections are published at different stages of editorial review.</p>
        <Link href="/methodology" className="inline-flex min-h-11 items-center font-semibold text-[color:var(--stage-accent)] hover:underline">
          See live corpus status →
        </Link>
      </div>

      {books.length > 0 ? (
        <div className="library-shelf mt-14 grid gap-x-8 gap-y-16 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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
