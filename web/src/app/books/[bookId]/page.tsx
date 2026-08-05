import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import { getBook, getBookKitabs } from "@/lib/api/books";
import { formatArabicTitle } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import { INDEXED_SOURCE_BOOK_IDS } from "@/lib/corpus";
import { ContentBadge } from "@/components/books/ContentBadge";
import { getEditionCover } from "@/components/books/BookCard";
import { corpusMaturity } from "@/lib/corpus-maturity";
import type { Metadata } from "next";

export const dynamic = "force-dynamic";

const ENGLISH_TITLES: Record<string, string> = {
  "11005": "Al-Kafi",
  "10083": "Tahdhib al-Ahkam",
  "11021": "Man La Yahduruhu al-Faqih",
  "11002": "Al-Istibsar",
  "71860": "Bihar al-Anwar",
  "11025": "Wasa'il al-Shia",
  "14036": "Mu'jam Rijal al-Hadith",
};

export async function generateMetadata({ params }: { params: Promise<{ bookId: string }> }): Promise<Metadata> {
  const { bookId } = await params;
  const book = await getBook(Number(bookId));
  if (!book) return { title: "Collection not found" };
  const title = ENGLISH_TITLES[book.source_book_id] ?? book.title_normalised;
  return {
    title,
    description: `Read ${title} with printed-page provenance and available hadith-level research data.`,
    alternates: { canonical: `/books/${book.id}` },
  };
}

export default async function BookDetailPage({ params }: { params: Promise<{ bookId: string }> }) {
  const { bookId } = await params;
  const book = await getBook(Number(bookId));
  if (!book) notFound();
  const title = formatArabicTitle(book.title_original);
  const englishTitle = ENGLISH_TITLES[book.source_book_id] ?? "Library volume";
  const maturity = corpusMaturity(book.source_book_id);
  const cover = getEditionCover(book.source_book_id);
  const hasStructuredContents = ["11005", "11021"].includes(book.source_book_id);
  const kitabs = hasStructuredContents ? await getBookKitabs(book.id) : [];
  const firstKitab = kitabs.find((kitab) => kitab.first_chapter_id !== null);
  const chapterReaderHref = firstKitab
    ? `/read/${book.id}/kitab/${encodeURIComponent(firstKitab.kitab_id)}/${firstKitab.first_chapter_id}?v=${firstKitab.volume}`
    : `/read/${book.id}/bab/1`;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
      <nav className="text-sm text-muted" aria-label="Breadcrumb">
        <Link href="/books" className="hover:text-accent">Library</Link>
        <span className="mx-2 text-border-strong">/</span>
        <span>{englishTitle}</span>
      </nav>

      <div className="mt-6 grid gap-8 border-t border-border pt-8 lg:grid-cols-[12rem_minmax(0,1fr)_16rem] lg:gap-10">
        <figure className="mx-auto w-full max-w-44 lg:mx-0">
          <div className="relative aspect-[0.72] overflow-hidden rounded-sm border border-border bg-surface-2">
            {cover?.src ? (
              <Image
                src={cover.src}
                alt={`${englishTitle} - cover of the catalogued edition`}
                fill
                priority
                sizes="(max-width: 1023px) 11rem, 12rem"
                className="object-contain"
              />
            ) : (
              <div className="flex h-full flex-col items-center justify-center p-4 text-center">
                <span className="font-mono text-[10px] text-muted">SOURCE {book.source_book_id}</span>
                <span className="mt-3 text-xs font-semibold text-foreground">Cover scan unavailable</span>
              </div>
            )}
          </div>
          <figcaption className="mt-2 text-xs leading-5 text-muted">
            {cover?.src ? "Catalogued edition cover" : "Archival placeholder"}
          </figcaption>
        </figure>

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <ContentBadge hasContent={book.has_content} />
            {maturity ? <Link href="/methodology" className="inline-flex min-h-6 items-center rounded-full border border-accent/30 bg-badge-verified px-3 text-xs font-semibold text-accent hover:underline">{maturity.label}</Link> : null}
            <span className="font-mono text-xs text-muted">SOURCE {book.source_book_id}</span>
          </div>
          <h1 className="mt-5 max-w-full break-words font-serif text-3xl font-semibold sm:text-4xl">{englishTitle}</h1>
          <p dir="rtl" lang="ar" className={`${amiri.className} mt-4 max-w-full overflow-hidden break-words text-right text-3xl leading-relaxed text-accent sm:text-4xl`}>
            {title}
          </p>

          {book.authors.length > 0 ? (
            <div className="mt-5 border-y border-border py-3">
              <p className="text-xs font-semibold text-muted">Author</p>
              <p dir="rtl" lang="ar" className={`${amiri.className} mt-1 max-w-full overflow-hidden break-words text-left text-xl text-foreground`}>
                {book.authors.map((author) => formatArabicTitle(author.name_original)).join(" — ")}
              </p>
            </div>
          ) : null}

          <div className="mt-7 flex flex-wrap items-center gap-3">
            {book.has_content && hasStructuredContents ? (
              <>
                <Link href={`/books/${book.id}/contents`} className="rounded-md bg-accent px-5 py-3 font-semibold text-accent-foreground hover:bg-accent-strong">
                  Browse contents
                </Link>
                <Link href={chapterReaderHref} className="rounded-md border border-border bg-surface px-5 py-3 font-medium text-foreground hover:border-accent hover:text-accent">
                  Read by chapter
                </Link>
                <Link href={`/read/${book.id}/1/1`} className="rounded-md border border-border bg-surface px-5 py-3 font-medium text-foreground hover:border-accent hover:text-accent">
                  Printed pages
                </Link>
              </>
            ) : book.has_content && INDEXED_SOURCE_BOOK_IDS.has(book.source_book_id) ? (
              <>
                <Link href={`/read/${book.id}/bab/1`} className="rounded-md bg-accent px-5 py-3 font-semibold text-accent-foreground hover:bg-accent-strong">
                  Read by chapter
                </Link>
                <Link href={`/read/${book.id}/1/1`} className="rounded-md border border-border bg-surface px-5 py-3 font-medium text-foreground hover:border-accent hover:text-accent">
                  Browse printed pages
                </Link>
              </>
            ) : book.has_content ? (
              <Link href={`/read/${book.id}/1/1`} className="rounded-md bg-accent px-5 py-3 font-semibold text-accent-foreground hover:bg-accent-strong">Start reading</Link>
            ) : (
            <p className="border border-border bg-surface px-4 py-3 text-sm leading-7 text-muted">
              Full text has not been digitised here yet. <a href={book.source_url} target="_blank" rel="noopener noreferrer" className="font-semibold text-accent hover:underline">View the original source.</a>
            </p>
          )}
          </div>
          {maturity ? <p className="mt-5 max-w-2xl text-sm leading-7 text-muted">{maturity.summary} <Link href="/methodology" className="font-semibold text-accent hover:underline">Review live corpus counts.</Link></p> : null}
        </div>

        <aside className="border-t border-border pt-5 lg:border-l lg:border-t-0 lg:pl-7 lg:pt-0">
          <h2 className="text-xs font-semibold text-foreground">Bibliographic record</h2>
          <dl className="mt-5 divide-y divide-border text-sm">
            <div className="grid grid-cols-[6rem_1fr] gap-3 py-3">
              <dt className="text-muted">Volumes</dt>
              <dd>{book.volume_count ?? "Not recorded"}</dd>
            </div>
            <div className="grid grid-cols-[6rem_1fr] gap-3 py-3">
              <dt className="text-muted">Language</dt>
              <dd>{book.language ?? "Arabic"}</dd>
            </div>
            {book.category ? (
              <div className="grid grid-cols-[6rem_1fr] gap-3 py-3">
                <dt className="text-muted">Category</dt>
                <dd dir="rtl" lang="ar" className={amiri.className}>{book.category.name_original}</dd>
              </div>
            ) : null}
            <div className="grid grid-cols-[6rem_1fr] gap-3 py-3">
              <dt className="text-muted">Edition</dt>
              <dd>eShia digital source</dd>
            </div>
          </dl>
          <a href={book.source_url} target="_blank" rel="noopener noreferrer" className="mt-5 inline-flex text-sm font-semibold text-accent hover:underline">Open source record ↗</a>
        </aside>
      </div>
    </div>
  );
}
