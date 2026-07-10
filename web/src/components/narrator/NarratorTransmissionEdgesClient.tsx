"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type {
  NarratorBookAppearanceCountRead,
  NarratorTransmissionEdgeRead,
  NarratorTransmissionEdgesRead,
  NarratorTransmissionSampleRead,
} from "@/lib/api/types";
import { formatArabicText } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const EDGE_LIMIT = 50;
const SAMPLE_LIMIT = 5;

function sampleLocation(sample: NarratorTransmissionSampleRead): string {
  const page =
    sample.page_start === sample.page_end
      ? `p. ${sample.page_start}`
      : `pp. ${sample.page_start}-${sample.page_end}`;
  return [
    `vol. ${sample.volume_start ?? "?"}`,
    page,
    sample.printed_number ? `no. ${sample.printed_number}` : null,
  ]
    .filter(Boolean)
    .join(" / ");
}

async function fetchEdges(params: {
  narratorId: number;
  sourceBookId: string | null;
}): Promise<NarratorTransmissionEdgesRead> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  query.set("limit", String(EDGE_LIMIT));
  query.set("sample_limit", String(SAMPLE_LIMIT));
  const response = await fetch(
    `${API_BASE_URL}/narrators/${params.narratorId}/transmission-edges?${query.toString()}`
  );
  if (!response.ok) throw new Error(response.statusText || "Could not load transmission graph");
  return response.json() as Promise<NarratorTransmissionEdgesRead>;
}

function SampleLink({ sample }: { sample: NarratorTransmissionSampleRead }) {
  return (
    <li className="rounded-lg border border-border bg-background p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <Link
          href={`/hadith/${encodeURIComponent(sample.public_id)}`}
          className="font-mono text-xs text-accent hover:underline"
        >
          {sample.public_id}
        </Link>
        <Link
          href={`/read/${sample.book_id}/${sample.volume_start ?? 1}/${sample.page_start}#hadith-${sample.hadith_id}`}
          className="text-xs font-medium text-accent hover:underline"
        >
          Reader
        </Link>
      </div>
      <p className="mt-1 text-xs text-muted">{sampleLocation(sample)}</p>
      <p dir="rtl" lang="ar" className={`${amiri.className} mt-2 text-right text-lg leading-loose`}>
        {formatArabicText(sample.raw_token)}{" "}
        <span className="text-muted">/</span>{" "}
        {formatArabicText(sample.related_raw_token)}
      </p>
      <p dir="rtl" lang="ar" className={`${amiri.className} mt-1 text-right text-base text-muted`}>
        {formatArabicText(sample.matn_excerpt)}
      </p>
    </li>
  );
}

function EdgeCard({ edge }: { edge: NarratorTransmissionEdgeRead }) {
  return (
    <article className="rounded-lg border border-border bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <Link
          href={`/narrators/${edge.related_narrator.id}`}
          dir="rtl"
          lang="ar"
          className={`${amiri.className} text-right text-2xl font-semibold text-accent hover:underline`}
        >
          {formatArabicText(edge.related_narrator.canonical_name_ar)}
        </Link>
        <span className="rounded-full bg-badge-verified px-3 py-1 text-sm text-accent">
          {edge.total} hadiths
        </span>
      </div>

      {edge.book_counts.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {edge.book_counts.map((count) => (
            <span key={count.source_book_id} className="rounded-full bg-badge px-2 py-0.5 text-xs text-muted">
              {count.title_original}: {count.total}
            </span>
          ))}
        </div>
      ) : null}

      {edge.samples.length ? (
        <ul className="mt-3 space-y-2">
          {edge.samples.map((sample) => (
            <SampleLink key={`${sample.hadith_id}-${sample.node_id}-${sample.related_node_id}`} sample={sample} />
          ))}
        </ul>
      ) : null}
    </article>
  );
}

function EdgeList({
  title,
  note,
  empty,
  edges,
}: {
  title: string;
  note: string;
  empty: string;
  edges: NarratorTransmissionEdgeRead[];
}) {
  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-sm font-semibold tracking-wide text-muted uppercase">{title}</h3>
        <p className="mt-1 text-sm text-muted">{note}</p>
      </div>
      {edges.length ? (
        <div className="space-y-3">
          {edges.map((edge) => (
            <EdgeCard key={edge.related_narrator.id} edge={edge} />
          ))}
        </div>
      ) : (
        <p className="rounded-lg border border-border bg-surface p-4 text-sm text-muted">{empty}</p>
      )}
    </div>
  );
}

export function NarratorTransmissionEdgesClient({
  narratorId,
  counts,
  initialEdges,
  initialSourceBookId,
}: {
  narratorId: number;
  counts: NarratorBookAppearanceCountRead[];
  initialEdges: NarratorTransmissionEdgesRead | null;
  initialSourceBookId: string | null;
}) {
  const [sourceBookId, setSourceBookId] = useState<string | null>(initialSourceBookId);
  const [edges, setEdges] = useState<NarratorTransmissionEdgesRead | null>(initialEdges);
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
      const nextEdges = await fetchEdges({ narratorId, sourceBookId: nextSourceBookId });
      setSourceBookId(nextSourceBookId);
      setEdges(nextEdges);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load transmission graph");
    } finally {
      setLoading(false);
    }
  }

  const teachers = edges?.teachers ?? [];
  const students = edges?.students ?? [];

  return (
    <section className="mt-8 space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold tracking-wide text-muted uppercase">Transmission graph</h2>
          <p className="mt-1 text-sm text-muted">
            Showing adjacent resolved narrators in {selectedLabel}. Counts are distinct hadiths.
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
            All books
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

      <div className="grid gap-4 lg:grid-cols-2">
        <EdgeList
          title="Narrates from"
          note="The next resolved node in the chain."
          empty="No adjacent teachers are resolved for this scope yet."
          edges={teachers}
        />
        <EdgeList
          title="Narrated by"
          note="The previous resolved node in the chain."
          empty="No adjacent students are resolved for this scope yet."
          edges={students}
        />
      </div>

      {message ? <p className="text-sm text-muted">{message}</p> : null}
      {loading ? <p className="text-sm text-muted">Loading graph...</p> : null}
    </section>
  );
}
