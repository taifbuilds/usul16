import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook, getBookKitabs } from "@/lib/api/books";
import { formatArabicTitle } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import { KitabCard } from "@/components/books/KitabCard";
import { EmptyState } from "@/components/ui/EmptyState";

export const dynamic = "force-dynamic";

// Book contents overview: kitabs (book-sections) grouped by printed volume,
// each opening to its chapter list. This is the holistic map of the collection.
export default async function BookContentsPage({
  params,
}: {
  params: Promise<{ bookId: string }>;
}) {
  const { bookId: bookIdParam } = await params;
  const bookId = Number(bookIdParam);

  const book = await getBook(bookId);
  if (!book) notFound();
  const title = formatArabicTitle(book.title_original);

  const kitabs = await getBookKitabs(bookId);
  if (!kitabs.length) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
        <EmptyState
          title="No structured contents yet"
          description={`"${book.title_normalised}" doesn't have a kitab/chapter index. Try the chapter or printed-page reader instead.`}
        />
      </div>
    );
  }

  const volumes = [...new Set(kitabs.map((k) => k.volume))].sort((a, b) => a - b);

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <nav className="text-sm text-muted" aria-label="Breadcrumb">
        <Link href="/books" className="hover:text-accent">Library</Link>
        <span className="mx-2 text-border-strong">/</span>
        <Link href={`/books/${bookId}`} className="hover:text-accent">
          {book.title_normalised}
        </Link>
        <span className="mx-2 text-border-strong">/</span>
        <span>Contents</span>
      </nav>

      <div className="mt-6 flex flex-wrap items-baseline justify-between gap-3 border-b border-border pb-6">
        <h1 className="font-serif text-3xl font-semibold sm:text-4xl">Contents</h1>
        <p dir="rtl" lang="ar" className={`${amiri.className} text-2xl text-accent`}>
          {title}
        </p>
      </div>

      <div className="mt-8 space-y-10">
        {volumes.map((volume) => (
          <section key={volume}>
            <h2 className="mb-4 text-xs font-semibold uppercase tracking-wide text-muted">
              Volume {volume}
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {kitabs
                .filter((k) => k.volume === volume)
                .map((kitab) => (
                  <KitabCard
                    key={`${kitab.volume}-${kitab.kitab_id}`}
                    kitab={kitab}
                    href={`/books/${bookId}/kitab/${encodeURIComponent(kitab.kitab_id)}`}
                  />
                ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
