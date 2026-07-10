import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook, getBookChapters, getChapterHadiths } from "@/lib/api/books";
import { formatArabicTitle, formatArabicText } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import { ChapterPicker } from "@/components/reader/ChapterPicker";
import { ReaderNav, type NavTarget } from "@/components/reader/ReaderNav";
import { IndexedHadithCard, SectionHeading } from "@/components/reader/ReaderText";
import { EmptyState } from "@/components/ui/EmptyState";

export const dynamic = "force-dynamic";

// Chapter-flow reader: the hadith — never the printed page — is the reading
// unit. Every hadith renders complete (page-spanning ones included); printed
// volume/page live on each card as a citation link into the page view.
export default async function ChapterReaderPage({
  params,
}: {
  params: Promise<{ bookId: string; chapter: string }>;
}) {
  const { bookId: bookIdParam, chapter: chapterParam } = await params;
  const bookId = Number(bookIdParam);
  const chapterIndex = Number(chapterParam);

  const book = await getBook(bookId);
  if (!book) notFound();
  const title = formatArabicTitle(book.title_original);

  const chapters = await getBookChapters(bookId);
  if (!chapters.length) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
        <EmptyState
          title="No indexed hadiths for this book yet"
          description={`"${title}" doesn't have extracted hadith records, so chapter reading isn't available. Try the page-by-page reader instead.`}
        />
      </div>
    );
  }

  const chapter = chapters.find((c) => c.index === chapterIndex);
  if (!chapter) notFound();
  const hadiths = await getChapterHadiths(bookId, chapterIndex);
  if (!hadiths) notFound();

  const prevChapter = chapters.find((c) => c.index === chapterIndex - 1) ?? null;
  const nextChapter = chapters.find((c) => c.index === chapterIndex + 1) ?? null;
  const prev: NavTarget | null = prevChapter
    ? { href: `/read/${bookId}/bab/${prevChapter.index}`, label: "Previous chapter" }
    : null;
  const next: NavTarget | null = nextChapter
    ? { href: `/read/${bookId}/bab/${nextChapter.index}`, label: "Next chapter" }
    : null;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <Link href={`/books/${bookId}`} className="text-sm font-medium text-accent hover:underline">
          ← {book.title_normalised}
        </Link>
        <p dir="rtl" lang="ar" className={`${amiri.className} text-xl text-accent`}>
          {title}
        </p>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <ChapterPicker bookId={bookId} chapters={chapters} currentIndex={chapterIndex} />
        <Link
          href={`/read/${bookId}/${chapter.volume ?? 1}/${chapter.page_start}`}
          className="shrink-0 text-sm text-muted hover:text-accent hover:underline"
        >
          Printed-page view →
        </Link>
      </div>

      <div dir="rtl" lang="ar" className={`${amiri.className} mt-6 space-y-5 text-right`}>
        {chapter.title ? <SectionHeading text={formatArabicText(chapter.title)} /> : null}
        {hadiths.map((hadith) => (
          <IndexedHadithCard key={hadith.id} hadith={hadith} />
        ))}
      </div>

      <div className="mt-8">
        <ReaderNav
          prev={prev}
          next={next}
          position={`Chapter ${chapterIndex} of ${chapters.length} · ${chapter.hadith_count} hadith${chapter.hadith_count === 1 ? "" : "s"}`}
        />
      </div>
    </div>
  );
}
