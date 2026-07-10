import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook, getBookChapters, getHadith } from "@/lib/api/books";
import { formatArabicTitle } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import { IndexedHadithCard } from "@/components/reader/ReaderText";

export const dynamic = "force-dynamic";

// Permanent home of a single hadith: one stable URL per hadith record. This
// ID is what cross-referencing ("this hadith IS that hadith"), grading and
// the MCP tools will point at.
export default async function HadithPermalinkPage({
  params,
}: {
  params: Promise<{ publicId: string }>;
}) {
  const { publicId } = await params;
  const hadith = await getHadith(decodeURIComponent(publicId));
  if (!hadith) notFound();

  const book = await getBook(hadith.book_id);
  const title = book ? formatArabicTitle(book.title_original) : null;

  // Locate the containing chapter for "read in context".
  let contextHref: string | null = null;
  let chapterTitle: string | null = null;
  if (book) {
    const chapters = await getBookChapters(book.id);
    const chapter = chapters.find(
      (c) =>
        c.start_sequence <= hadith.sequence_in_book && hadith.sequence_in_book <= c.end_sequence
    );
    if (chapter) {
      contextHref = `/read/${book.id}/bab/${chapter.index}#hadith-${hadith.id}`;
      chapterTitle = chapter.title;
    }
  }

  const citation = [
    book?.title_normalised,
    hadith.volume_start !== null ? `vol. ${hadith.volume_start}` : null,
    hadith.page_end !== hadith.page_start
      ? `pp. ${hadith.page_start}-${hadith.page_end}`
      : `p. ${hadith.page_start}`,
    hadith.printed_number ? `no. ${hadith.printed_number}` : null,
  ]
    .filter(Boolean)
    .join(", ");

  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <p className="text-xs tracking-wide text-muted/70 uppercase">Hadith record</p>
          <p className="mt-1 font-mono text-sm text-accent">{hadith.public_id}</p>
        </div>
        {title ? (
          <p dir="rtl" lang="ar" className={`${amiri.className} text-xl text-accent`}>
            {title}
          </p>
        ) : null}
      </div>

      {chapterTitle ? (
        <p dir="rtl" lang="ar" className={`${amiri.className} mt-3 text-right text-muted`}>
          {chapterTitle}
        </p>
      ) : null}

      <div dir="rtl" lang="ar" className={`${amiri.className} mt-6 text-right`}>
        <IndexedHadithCard hadith={hadith} />
      </div>

      <div className="mt-6 rounded-2xl border border-border bg-surface px-5 py-4 text-sm">
        <p className="font-medium text-muted">Citation</p>
        <p className="mt-1">{citation}</p>
        <p className="mt-1 font-mono text-xs text-muted">{hadith.public_id}</p>
      </div>

      <div className="mt-6 flex flex-wrap gap-4 text-sm">
        {contextHref ? (
          <Link href={contextHref} className="font-medium text-accent hover:underline">
            Read in chapter context →
          </Link>
        ) : null}
        <Link
          href={`/read/${hadith.book_id}/${hadith.volume_start ?? 1}/${hadith.page_start}`}
          className="text-muted hover:text-accent hover:underline"
        >
          Printed-page view
        </Link>
        <a
          href={hadith.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-muted hover:text-accent hover:underline"
        >
          Original source
        </a>
      </div>
    </div>
  );
}
