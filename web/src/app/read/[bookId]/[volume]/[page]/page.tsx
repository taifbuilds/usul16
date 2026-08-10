import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook, getBookHadiths, getBookPageIndex, getPage } from "@/lib/api/books";
import { formatArabicTitle } from "@/lib/arabic";
import { INDEXED_SOURCE_BOOK_IDS } from "@/lib/corpus";
import { Citation } from "@/components/citation/Citation";
import { ReaderNav, type NavTarget } from "@/components/reader/ReaderNav";
import { ReaderControls } from "@/components/reader/ReaderControls";
import { ReaderText } from "@/components/reader/ReaderText";
import { EmptyState } from "@/components/ui/EmptyState";

export const dynamic = "force-dynamic";

export default async function ReaderPage({
  params,
}: {
  params: Promise<{ bookId: string; volume: string; page: string }>;
}) {
  const { bookId: bookIdParam, volume: volumeParam, page: pageParam } = await params;
  const bookId = Number(bookIdParam);
  const volumeNumber = Number(volumeParam);
  const pageNumber = Number(pageParam);

  const book = await getBook(bookId);
  if (!book) notFound();
  const title = formatArabicTitle(book.title_original);

  const pages = await getBookPageIndex(bookId, { volume: volumeNumber });
  const index = pages.findIndex((p) => p.page_number === pageNumber);
  const pageSummary = index === -1 ? null : pages[index];

  if (!pageSummary) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
        <EmptyState
          title="This page hasn't been digitized yet"
          description={`Volume ${volumeNumber}, page ${pageNumber} of "${title}" isn't available yet.`}
        />
      </div>
    );
  }

  const page = await getPage(pageSummary.id);
  if (!page) notFound();
  const isIndexed = INDEXED_SOURCE_BOOK_IDS.has(book.source_book_id);
  const hadiths = isIndexed
    ? await getBookHadiths(bookId, { volume: volumeNumber, page: pageNumber })
    : undefined;

  // A printed page can carry the end of one chapter and the beginning of
  // another. Derive its context from the hadiths actually shown on the page,
  // rather than guessing from the last chapter whose first printed page falls
  // before this one. Al-Kafi has a verified kitab/chapter map, so use that
  // precise reader whenever it is available.
  const chapterContexts = isIndexed && hadiths
    ? Array.from(
        new Map(
          hadiths.flatMap((hadith) => {
            const structure = hadith.structure;
            if (!structure || structure.mapping_status !== "matched" || structure.volume === null) return [];
            const href = `/read/${bookId}/kitab/${encodeURIComponent(structure.kitab_id)}/${structure.chapter_id}?v=${structure.volume}`;
            return [[href, structure.chapter_name_en || structure.kitab_name_en] as const];
          })
        ).entries()
      )
    : [];
  const availablePages = pages.map((item) => item.page_number);
  const lastPageNumber = Math.max(...availablePages, pageNumber);
  const volumeCount = book.volume_count ?? volumeNumber;
  const atFirstOfVolume = index === 0;
  const atLastOfVolume = index === pages.length - 1;

  let prev: NavTarget | null = null;
  if (!atFirstOfVolume) {
    prev = { href: `/read/${bookId}/${volumeNumber}/${pages[index - 1].page_number}`, label: "Previous page" };
  } else if (volumeNumber > 1) {
    prev = { href: `/read/${bookId}/${volumeNumber - 1}/1`, label: "Previous volume" };
  }

  let next: NavTarget | null = null;
  if (!atLastOfVolume) {
    next = { href: `/read/${bookId}/${volumeNumber}/${pages[index + 1].page_number}`, label: "Next page" };
  } else if (book.volume_count !== null && volumeNumber < book.volume_count) {
    next = { href: `/read/${bookId}/${volumeNumber + 1}/1`, label: "Next volume" };
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-12">
      <h1 className="sr-only">{title}, volume {volumeNumber}, page {pageNumber}</h1>
      <div className="border-b border-border pb-4">
        <Citation
          title={title}
          volumeNumber={page.volume_number}
          pageNumber={page.page_number}
          sourceUrl={page.source_url}
          permanentPath={`/read/${bookId}/${volumeNumber}/${pageNumber}`}
        />
      </div>

      <div className="mt-4 border border-border bg-surface px-3 py-3 sm:px-4">
        <ReaderControls
          bookId={bookId}
          volumeNumber={volumeNumber}
          pageNumber={pageNumber}
          volumeCount={volumeCount}
          availablePages={availablePages}
        />
      </div>

      {chapterContexts.length > 0 ? (
        <div className="mt-3 flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm text-muted">
          <span>Chapter context:</span>
          {chapterContexts.map(([href, label], index) => (
            <span key={href}>
              {index > 0 ? <span className="mr-2 text-border-strong">/</span> : null}
              <Link href={href} className="font-medium text-accent hover:underline">
                {label}
              </Link>
            </span>
          ))}
        </div>
      ) : null}

      <div className="mx-auto mt-7 min-h-[45vh] max-w-3xl">
        <ReaderText page={page} hadiths={hadiths} bookTitle={book.title_original} />
      </div>

      <div className="mt-8">
        <ReaderNav prev={prev} next={next} position={`Volume ${volumeNumber} · Page ${pageNumber} of ${lastPageNumber}`} />
      </div>
    </div>
  );
}
