"use client";

import { useRouter } from "next/navigation";
import type { ChapterSummary } from "@/lib/api/types";

export function ChapterPicker({
  bookId,
  chapters,
  currentIndex,
}: {
  bookId: number;
  chapters: ChapterSummary[];
  currentIndex: number;
}) {
  const router = useRouter();

  return (
    <label className="flex min-w-0 items-center gap-2 text-sm text-muted">
      <span className="shrink-0">الباب</span>
      <select
        dir="rtl"
        value={currentIndex}
        onChange={(event) => router.push(`/read/${bookId}/bab/${event.target.value}`)}
        className="min-w-0 max-w-full flex-1 truncate rounded-lg border border-border bg-surface px-3 py-2 text-foreground"
      >
        {chapters.map((chapter) => (
          <option key={chapter.index} value={chapter.index}>
            {chapter.index}. {chapter.title ?? "(بدون عنوان)"}
          </option>
        ))}
      </select>
    </label>
  );
}
