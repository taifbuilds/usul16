"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type {
  NarratorBookAppearanceCountRead,
  NarratorHadithAppearancePage,
  NarratorHadithAppearanceRead,
} from "@/lib/api/types";
import { formatArabicText } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const PAGE_SIZE = 120;

function appearanceLocation(appearance: NarratorHadithAppearanceRead): string {
  const page =
    appearance.page_start === appearance.page_end
      ? `p. ${appearance.page_start}`
      : `pp. ${appearance.page_start}-${appearance.page_end}`;
  return [
    `vol. ${appearance.volume_start ?? "?"}`,
    page,
    appearance.printed_number ? `no. ${appearance.printed_number}` : null,
  ]
    .filter(Boolean)
    .join(" / ");
}

async function fetchAppearances(params: {
  narratorId: number;
  sourceBookId: string | null;
  skip: number;
  limit: number;
}): Promise<NarratorHadithAppearancePage> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  query.set("skip", String(params.skip));
  query.set("limit", String(params.limit));
  const response = await fetch(
    `${API_BASE_URL}/narrators/${params.narratorId}/hadith-appearances?${query.toString()}`
  );
  if (!response.ok) throw new Error(response.statusText || "Could not load appearances");
  return response.json() as Promise<NarratorHadithAppearancePage>;
}

function AppearanceCard({ appearance }: { appearance: NarratorHadithAppearanceRead }) {
  return (
    <article className="rounded-lg border border-border bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href={`/hadith/${encodeURIComponent(appearance.public_id)}`}
            className="font-mono text-sm text-accent hover:underline"
          >
            {appearance.public_id}
          </Link>
          <p className="mt-1 text-xs text-muted">{appearance.book_title}</p>
          <p className="mt-0.5 text-xs text-muted">{appearanceLocation(appearance)}</p>
        </div>
        <Link
          href={`/read/${appearance.book_id}/${appearance.volume_start ?? 1}/${appearance.page_start}#hadith-${appearance.hadith_id}`}
          className="text-xs font-medium text-accent hover:underline"
        >
          Open in reader
        </Link>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted">
        <span className="rounded-full bg-badge px-2 py-0.5">chain {appearance.chain_number}</span>
        <span className="rounded-full bg-badge px-2 py-0.5">node {appearance.node_position + 1}</span>
        {appearance.confidence !== null ? (
          <span className="rounded-full bg-badge-verified px-2 py-0.5 text-accent">
            {appearance.confidence}% {appearance.resolution_method ?? "resolved"}
          </span>
        ) : null}
      </div>
      {appearance.section_title ? (
        <p dir="rtl" lang="ar" className={`${amiri.className} mt-3 text-right text-base text-muted`}>
          {formatArabicText(appearance.section_title)}
        </p>
      ) : null}
      <p dir="rtl" lang="ar" className={`${amiri.className} mt-2 text-right text-lg leading-loose`}>
        {formatArabicText(appearance.matn_excerpt)}
      </p>
    </article>
  );
}

export function NarratorAppearancesClient({
  narratorId,
  counts,
  initialAppearances,
  initialTotal,
}: {
  narratorId: number;
  counts: NarratorBookAppearanceCountRead[];
  initialAppearances: NarratorHadithAppearanceRead[];
  initialTotal: number;
}) {
  const [sourceBookId, setSourceBookId] = useState<string | null>(null);
  const [appearances, setAppearances] = useState(initialAppearances);
  const [total, setTotal] = useState(initialTotal);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const selectedLabel = useMemo(() => {
    if (!sourceBookId) return "all books";
    return counts.find((count) => count.source_book_id === sourceBookId)?.title_original ?? sourceBookId;
  }, [counts, sourceBookId]);

  async function loadFilter(nextSourceBookId: string | null) {
    setLoading(true);
    setMessage(null);
    try {
      const page = await fetchAppearances({
        narratorId,
        sourceBookId: nextSourceBookId,
        skip: 0,
        limit: PAGE_SIZE,
      });
      setSourceBookId(nextSourceBookId);
      setAppearances(page.appearances);
      setTotal(page.total);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load appearances");
    } finally {
      setLoading(false);
    }
  }

  async function loadMore() {
    setLoading(true);
    setMessage(null);
    try {
      const page = await fetchAppearances({
        narratorId,
        sourceBookId,
        skip: appearances.length,
        limit: PAGE_SIZE,
      });
      setAppearances((current) => [...current, ...page.appearances]);
      setTotal(page.total);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load more appearances");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mt-8 space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold tracking-wide text-muted uppercase">Hadith appearances</h2>
          <p className="mt-1 text-sm text-muted">
            Showing {appearances.length} of {total} resolved hadiths in {selectedLabel}.
          </p>
        </div>
      </div>

      {counts.length ? (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void loadFilter(null)}
            disabled={loading}
            className={`rounded-full border px-3 py-1 text-sm ${
              sourceBookId === null
                ? "border-accent bg-badge-verified text-accent"
                : "border-border text-muted hover:border-accent hover:text-accent"
            }`}
          >
            All books: {initialTotal}
          </button>
          {counts.map((count) => (
            <button
              key={count.source_book_id}
              type="button"
              onClick={() => void loadFilter(count.source_book_id)}
              disabled={loading}
              className={`rounded-full border px-3 py-1 text-sm ${
                sourceBookId === count.source_book_id
                  ? "border-accent bg-badge-verified text-accent"
                  : "border-border text-muted hover:border-accent hover:text-accent"
              }`}
            >
              {count.title_original}: {count.total}
            </button>
          ))}
        </div>
      ) : null}

      {appearances.length ? (
        <div className="grid gap-3 lg:grid-cols-2">
          {appearances.map((appearance) => (
            <AppearanceCard key={`${appearance.hadith_id}-${appearance.node_id}`} appearance={appearance} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted">No resolved hadith appearances yet.</p>
      )}

      <div className="flex flex-wrap items-center gap-3">
        {appearances.length < total ? (
          <button
            type="button"
            onClick={() => void loadMore()}
            disabled={loading}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-accent hover:border-accent disabled:opacity-50"
          >
            {loading ? "Loading..." : "Load more"}
          </button>
        ) : null}
        {message ? <p className="text-sm text-muted">{message}</p> : null}
      </div>
    </section>
  );
}
