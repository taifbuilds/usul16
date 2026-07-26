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
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-12">
      <header className="border-b border-border pb-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-xs font-semibold text-muted">Hadith record</h1>
          <p className="mt-1 font-mono text-sm text-accent">{hadith.public_id}</p>
        </div>
        {title ? (
          <p dir="rtl" lang="ar" className={`${amiri.className} max-w-full text-right text-xl text-accent`}>
            {title}
          </p>
        ) : null}
      </div>

      {hadith.structure && hadith.structure.mapping_status === "matched" ? (
        <p className="mt-4 max-w-3xl text-sm leading-6 text-muted">
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
      </header>

      <div dir="rtl" lang="ar" className={`${amiri.className} mt-5 text-right sm:mt-6`}>
        <IndexedHadithCard hadith={hadith} />
      </div>

      <section className="mt-6 border-y border-border bg-surface-2 px-1 py-4 text-sm sm:px-5" aria-labelledby="citation-heading">
        <h2 id="citation-heading" className="mb-2 font-semibold text-foreground">Citation</h2>
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
      </section>

      <nav aria-label="Hadith record links" className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-sm">
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
      </nav>
    </div>
  );
}
