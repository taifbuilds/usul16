import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook, getBookChapters, getHadith } from "@/lib/api/books";
import { formatArabicTitle } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import { IndexedHadithCard } from "@/components/reader/ReaderText";
import { Citation } from "@/components/citation/Citation";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ publicId: string }> }): Promise<Metadata> {
  const { publicId } = await params;
  const hadith = await getHadith(decodeURIComponent(publicId));
  if (!hadith) return { title: "Hadith not found" };
  const book = await getBook(hadith.book_id);
  const work = book?.title_normalised ?? "Shia hadith";
  return {
    title: `${work} · Hadith ${hadith.printed_number ?? hadith.public_id}`,
    description: `Source record ${hadith.public_id}, volume ${hadith.volume_start ?? "unknown"}, page ${hadith.page_start}.`,
    alternates: { canonical: `/hadith/${encodeURIComponent(hadith.public_id)}` },
  };
}

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

  // Locate the containing chapter for "read in context". Prefer the Thaqalayn
  // kitab/chapter structure when present; fall back to the section-title runs.
  let contextHref: string | null = null;
  let chapterTitle: string | null = null;
  let kitabHref: string | null = null;
  if (book && hadith.structure && hadith.structure.mapping_status === "matched") {
    const { kitab_id, kitab_name_en, chapter_id, chapter_name_en } = hadith.structure;
    contextHref = `/read/${book.id}/kitab/${encodeURIComponent(kitab_id)}/${chapter_id}#hadith-${hadith.id}`;
    kitabHref = `/books/${book.id}/kitab/${encodeURIComponent(kitab_id)}`;
    chapterTitle = chapter_name_en || kitab_name_en;
  } else if (book) {
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

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h1 className="text-xs font-semibold tracking-wide text-muted uppercase">Hadith record</h1>
          <p className="mt-1 font-mono text-sm text-accent">{hadith.public_id}</p>
        </div>
        {title ? (
          <p dir="rtl" lang="ar" className={`${amiri.className} text-xl text-accent`}>
            {title}
          </p>
        ) : null}
      </div>

      {hadith.structure && hadith.structure.mapping_status === "matched" ? (
        <p className="mt-3 text-sm text-muted">
          {kitabHref ? (
            <Link href={kitabHref} className="hover:text-accent hover:underline">
              {hadith.structure.kitab_name_en}
            </Link>
          ) : (
            hadith.structure.kitab_name_en
          )}
          {hadith.structure.chapter_name_en ? (
            <>
              <span className="mx-2 text-border-strong">/</span>
              {hadith.structure.chapter_name_en}
            </>
          ) : null}
          {hadith.structure.number_in_chapter !== null ? (
            <span className="ml-2 font-mono text-gold">#{hadith.structure.number_in_chapter}</span>
          ) : null}
        </p>
      ) : chapterTitle ? (
        <p dir="rtl" lang="ar" className={`${amiri.className} mt-3 text-right text-muted`}>
          {chapterTitle}
        </p>
      ) : null}

      <div dir="rtl" lang="ar" className={`${amiri.className} mt-6 text-right`}>
        <IndexedHadithCard hadith={hadith} />
      </div>

      <div className="mt-6 border border-border bg-surface px-5 py-4 text-sm">
        <p className="mb-2 font-medium text-muted">Citation</p>
        <Citation
          title={title ?? book?.title_normalised ?? "Shia hadith"}
          volumeNumber={hadith.volume_start}
          pageNumber={hadith.page_start}
          pageEnd={hadith.page_end}
          printedNumber={hadith.printed_number}
          publicId={hadith.public_id}
          permanentPath={`/hadith/${encodeURIComponent(hadith.public_id)}`}
          sourceUrl={hadith.source_url}
        />
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
