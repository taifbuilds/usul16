import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getBook,
  getBookKitabs,
  getKitabChapters,
  getKitabChapterHadiths,
} from "@/lib/api/books";
import { amiri } from "@/lib/fonts";
import { ReaderNav, type NavTarget } from "@/components/reader/ReaderNav";
import { IndexedHadithCard } from "@/components/reader/ReaderText";
import { EmptyState } from "@/components/ui/EmptyState";

export const dynamic = "force-dynamic";

// Numbered chapter reader: hadiths in their Thaqalayn chapter order, each with
// per-chapter number, verbatim English, and gradings. The printed-page view
// remains the provenance path, linked from every card.
export default async function KitabChapterReaderPage({
  params,
}: {
  params: Promise<{ bookId: string; kitabId: string; chapterId: string }>;
}) {
  const { bookId: bookIdParam, kitabId, chapterId: chapterIdParam } = await params;
  const bookId = Number(bookIdParam);
  const chapterId = Number(chapterIdParam);

  const book = await getBook(bookId);
  if (!book) notFound();

  const [kitabs, chapters, hadiths] = await Promise.all([
    getBookKitabs(bookId),
    getKitabChapters(bookId, kitabId),
    getKitabChapterHadiths(bookId, kitabId, chapterId),
  ]);
  if (!hadiths || !chapters) notFound();

  const kitab = kitabs.find((k) => k.kitab_id === kitabId) ?? null;
  const chapterOrder = chapters.map((c) => c.chapter_id);
  const currentPos = chapterOrder.indexOf(chapterId);
  if (currentPos === -1) notFound();
  const current = chapters[currentPos];
  const prevChapter = currentPos > 0 ? chapters[currentPos - 1] : null;
  const nextChapter =
    currentPos < chapters.length - 1 ? chapters[currentPos + 1] : null;

  const chapterHref = (id: number) =>
    `/read/${bookId}/kitab/${encodeURIComponent(kitabId)}/${id}`;
  const prev: NavTarget | null = prevChapter
    ? { href: chapterHref(prevChapter.chapter_id), label: "Previous chapter" }
    : null;
  const next: NavTarget | null = nextChapter
    ? { href: chapterHref(nextChapter.chapter_id), label: "Next chapter" }
    : null;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <nav className="text-sm text-muted" aria-label="Breadcrumb">
        <Link href={`/books/${bookId}/contents`} className="hover:text-accent">Contents</Link>
        <span className="mx-2 text-border-strong">/</span>
        <Link href={`/books/${bookId}/kitab/${encodeURIComponent(kitabId)}`} className="hover:text-accent">
          {kitab?.name_en ?? "Kitab"}
        </Link>
      </nav>

      <div className="mt-4 border-b border-border pb-5">
        <h1 className="font-serif text-2xl font-semibold leading-snug sm:text-3xl">
          {current.name_en || `Chapter ${chapterId}`}
        </h1>
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted">
          <span>
            {hadiths.length} hadith{hadiths.length === 1 ? "" : "s"}
          </span>
          {hadiths[0]?.volume_start ? (
            <>
              <span aria-hidden="true" className="text-border">·</span>
              <Link
                href={`/read/${bookId}/${hadiths[0].volume_start}/${hadiths[0].page_start}`}
                className="hover:text-accent hover:underline"
              >
                Printed-page view →
              </Link>
            </>
          ) : null}
        </div>
      </div>

      {hadiths.length === 0 ? (
        <div className="mt-8">
          <EmptyState title="No hadiths in this chapter" description="" />
        </div>
      ) : (
        <div dir="rtl" lang="ar" className={`${amiri.className} mt-6 space-y-5 text-right`}>
          {hadiths.map((hadith) => (
            <IndexedHadithCard key={hadith.id} hadith={hadith} />
          ))}
        </div>
      )}

      <div className="mt-8">
        <ReaderNav
          prev={prev}
          next={next}
          position={`Chapter ${currentPos + 1} of ${chapters.length}`}
        />
      </div>
    </div>
  );
}
