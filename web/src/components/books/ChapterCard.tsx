import Link from "next/link";
import type { ThaqalaynChapterSummary } from "@/lib/api/types";

export function ChapterCard({
  chapter,
  href,
}: {
  chapter: ThaqalaynChapterSummary;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="group flex flex-col justify-between gap-4 border border-border bg-surface p-4 transition hover:border-accent"
    >
      <p className="text-sm leading-6 text-foreground group-hover:text-accent">
        {chapter.name_en || `Chapter ${chapter.chapter_id}`}
      </p>
      <span className="text-xs text-muted">
        {chapter.hadith_count} hadith{chapter.hadith_count === 1 ? "" : "s"}
      </span>
    </Link>
  );
}
