import Link from "next/link";
import { getBooks } from "@/lib/api/books";
import { amiri } from "@/lib/fonts";
import { BookCard } from "@/components/books/BookCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { Pagination } from "@/components/ui/Pagination";

export const dynamic = "force-dynamic";

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

  return (
    <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold tracking-wide text-accent uppercase">The corpus</p>
          <h1 className="mt-2 font-serif text-4xl">The Library</h1>
        </div>
        <p dir="rtl" lang="ar" className={`${amiri.className} text-3xl text-gold`}>
          المكتبة
        </p>
      </div>
      <div className="mt-6 border-b border-border" />

      <div className="mt-6 flex gap-2 text-sm">
        <Link
          href="/books"
          className={`rounded-full px-3.5 py-1.5 font-medium ${
            view === "available" ? "bg-foreground text-background" : "border border-border text-muted"
          }`}
        >
          Available to read
        </Link>
        <Link
          href="/books?view=all"
          className={`rounded-full px-3.5 py-1.5 font-medium ${
            view === "all" ? "bg-foreground text-background" : "border border-border text-muted"
          }`}
        >
          All books (catalog)
        </Link>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {books.length > 0 ? (
          books.map((book, i) => <BookCard key={book.id} book={book} index={skip + i + 1} />)
        ) : (
          <div className="sm:col-span-2">
            <EmptyState
              title="No books found"
              description={
                view === "available"
                  ? "Nothing has been fully crawled yet."
                  : "The catalog appears to be empty — has metadata been crawled?"
              }
            />
          </div>
        )}
      </div>

      <div className="mt-6">
        <Pagination
          basePath="/books"
          skip={skip}
          limit={LIMIT}
          hasMore={books.length === LIMIT}
          extraParams={view === "all" ? { view: "all" } : {}}
        />
      </div>
    </div>
  );
}
