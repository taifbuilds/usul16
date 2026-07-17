import {
  getHadithSplitAudit,
  getHadithSplitReviewQueue,
  getHadithSplitReviewStats,
} from "@/lib/api/books";
import { SplitReviewClient } from "@/components/review/SplitReviewClient";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

const DEFAULT_SOURCE_BOOK_ID = "11005";

export default async function SplitReviewPage({
  searchParams,
}: {
  searchParams?: Promise<{ source_book_id?: string; limit?: string; flag?: string }>;
}) {
  if (process.env.ENABLE_REVIEW_UI !== "true") notFound();

  const params = searchParams ? await searchParams : {};
  const sourceBookId = params.source_book_id ?? DEFAULT_SOURCE_BOOK_ID;
  const limit = Number(params.limit ?? 30);
  const flag = params.flag ?? null;

  const [stats, audit, items] = await Promise.all([
    getHadithSplitReviewStats({ sourceBookId }),
    getHadithSplitAudit({ sourceBookId }),
    getHadithSplitReviewQueue({
      sourceBookId,
      status: "unreviewed",
      flag,
      suspiciousOnly: true,
      limit: Number.isFinite(limit) ? limit : 30,
    }),
  ]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-medium tracking-wide text-muted uppercase">Manual review</p>
          <h1 className="mt-1 font-serif text-3xl font-semibold text-accent">
            Hadith isnad/matn split queue
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Human-approved corrections live separately from extractor drafts, so rebuilds do not
            overwrite reviewed splits.
          </p>
        </div>
        <form className="flex flex-wrap items-end gap-3">
          <label className="block text-sm">
            <span className="font-medium text-muted">Source book ID</span>
            <input
              name="source_book_id"
              defaultValue={sourceBookId}
              className="mt-1 w-32 rounded-lg border border-border bg-surface px-3 py-2 outline-none focus:border-accent"
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium text-muted">Queue size</span>
            <input
              name="limit"
              type="number"
              min="1"
              max="100"
              defaultValue={Number.isFinite(limit) ? limit : 30}
              className="mt-1 w-28 rounded-lg border border-border bg-surface px-3 py-2 outline-none focus:border-accent"
            />
          </label>
          {flag ? <input type="hidden" name="flag" value={flag} /> : null}
          <button
            type="submit"
            className="rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-accent hover:border-accent"
          >
            Load
          </button>
        </form>
      </div>

      <SplitReviewClient
        initialItems={items}
        initialStats={stats}
        initialAudit={audit}
        initialFlag={flag}
        sourceBookId={sourceBookId}
        queueLimit={Number.isFinite(limit) ? limit : 30}
      />
    </div>
  );
}
