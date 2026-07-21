import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook, getBookKitabs, getKitabChapters } from "@/lib/api/books";
import { ChapterCard } from "@/components/books/ChapterCard";
import { EmptyState } from "@/components/ui/EmptyState";

export const dynamic = "force-dynamic";

// One kitab's chapter index: a grid of chapter cards, each opening the numbered
// reading page for that chapter.
export default async function KitabPage({
  params,
}: {
  params: Promise<{ bookId: string; kitabId: string }>;
}) {
  const { bookId: bookIdParam, kitabId } = await params;
  const bookId = Number(bookIdParam);

  const book = await getBook(bookId);
  if (!book) notFound();

  const [kitabs, chapters] = await Promise.all([
    getBookKitabs(bookId),
    getKitabChapters(bookId, kitabId),
  ]);
  if (!chapters) notFound();

  const kitab = kitabs.find((k) => k.kitab_id === kitabId) ?? null;

  if (!chapters.length) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
        <EmptyState title="No chapters in this kitab" description="This section has no indexed chapters yet." />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <nav className="text-sm text-muted" aria-label="Breadcrumb">
        <Link href="/books" className="hover:text-accent">Library</Link>
        <span className="mx-2 text-border-strong">/</span>
        <Link href={`/books/${bookId}`} className="hover:text-accent">{book.title_normalised}</Link>
        <span className="mx-2 text-border-strong">/</span>
        <Link href={`/books/${bookId}/contents`} className="hover:text-accent">Contents</Link>
        <span className="mx-2 text-border-strong">/</span>
        <span>{kitab?.name_en ?? "Kitab"}</span>
      </nav>

      <div className="mt-6 border-b border-border pb-6">
        <h1 className="font-serif text-3xl font-semibold sm:text-4xl">
          {kitab?.name_en ?? "Kitab"}
        </h1>
        <p className="mt-2 text-sm text-muted">
          {chapters.length} chapter{chapters.length === 1 ? "" : "s"}
          {kitab ? ` · ${kitab.hadith_count} hadiths` : ""}
        </p>
      </div>

      <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {chapters.map((chapter) => (
          <ChapterCard
            key={chapter.chapter_id}
            chapter={chapter}
            href={`/read/${bookId}/kitab/${encodeURIComponent(kitabId)}/${chapter.chapter_id}`}
          />
        ))}
      </div>
    </div>
  );
}
