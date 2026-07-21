import Link from "next/link";
import type { KitabSummary } from "@/lib/api/types";

export function KitabCard({ kitab, href }: { kitab: KitabSummary; href: string }) {
  return (
    <Link
      href={href}
      className="group flex flex-col gap-3 border border-border bg-surface p-5 transition hover:border-accent"
    >
      <h3 className="font-serif text-lg leading-snug text-foreground group-hover:text-accent">
        {kitab.name_en}
      </h3>
      <div className="mt-auto flex items-center gap-3 text-xs text-muted">
        <span>
          {kitab.chapter_count} chapter{kitab.chapter_count === 1 ? "" : "s"}
        </span>
        <span aria-hidden="true" className="text-border">·</span>
        <span>
          {kitab.hadith_count} hadith{kitab.hadith_count === 1 ? "" : "s"}
        </span>
      </div>
    </Link>
  );
}
