import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook } from "@/lib/api/books";
import { formatArabicTitle } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import { INDEXED_SOURCE_BOOK_IDS } from "@/lib/corpus";
import { ContentBadge } from "@/components/books/ContentBadge";

export const dynamic = "force-dynamic";

export default async function BookDetailPage({ params }: { params: Promise<{ bookId: string }> }) {
  const { bookId } = await params;
  const book = await getBook(Number(bookId));
  if (!book) notFound();
  const title = formatArabicTitle(book.title_original);

  return (
    <div className="mx-auto max-w-2xl px-4 py-14 sm:px-6">
      <ContentBadge hasContent={book.has_content} />

      <div className="mt-4 flex items-start justify-between gap-4">
        <h1 className="font-serif text-3xl">{book.title_normalised}</h1>
        <p dir="rtl" lang="ar" className={`${amiri.className} shrink-0 text-right text-2xl text-accent`}>
          {title}
        </p>
      </div>

      {book.authors.length > 0 ? (
        <p dir="rtl" lang="ar" className={`${amiri.className} mt-2 text-right text-muted`}>
          {book.authors.map((a) => formatArabicTitle(a.name_original)).join(" — ")}
        </p>
      ) : null}

      <dl className="mt-6 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 border-t border-border pt-4 text-sm text-muted">
        {book.category ? (
          <>
            <dt>Category</dt>
            <dd dir="rtl" lang="ar" className={amiri.className}>
              {book.category.name_original}
            </dd>
          </>
        ) : null}
        {book.volume_count ? (
          <>
            <dt>Volumes</dt>
            <dd>{book.volume_count}</dd>
          </>
        ) : null}
      </dl>

      <div className="mt-8">
        {book.has_content && INDEXED_SOURCE_BOOK_IDS.has(book.source_book_id) ? (
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href={`/read/${book.id}/bab/1`}
              className="inline-block rounded-full bg-foreground px-5 py-2.5 font-medium text-background hover:opacity-85"
            >
              Read by chapter →
            </Link>
            <Link
              href={`/read/${book.id}/1/1`}
              className="inline-block rounded-full border border-border px-5 py-2.5 font-medium text-muted hover:border-accent hover:text-accent"
            >
              Browse printed pages
            </Link>
          </div>
        ) : book.has_content ? (
          <Link
            href={`/read/${book.id}/1/1`}
            className="inline-block rounded-full bg-foreground px-5 py-2.5 font-medium text-background hover:opacity-85"
          >
            Start reading →
          </Link>
        ) : (
          <div className="rounded-2xl border border-dashed border-border px-5 py-4 text-sm text-muted">
            This book&apos;s full text hasn&apos;t been digitized here yet.{" "}
            <a href={book.source_url} target="_blank" rel="noopener noreferrer" className="font-medium text-accent hover:underline">
              View it on the original source
            </a>
            .
          </div>
        )}
      </div>
    </div>
  );
}
