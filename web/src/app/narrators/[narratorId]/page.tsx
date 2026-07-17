import Link from "next/link";
import { notFound } from "next/navigation";
import type { RijalEntryRead } from "@/lib/api/types";
import { getNarrator, getNarratorTransmissionEdges } from "@/lib/api/books";
import { formatArabicText } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import { NarratorAppearancesClient } from "@/components/narrator/NarratorAppearancesClient";
import { NarratorTransmissionEdgesClient } from "@/components/narrator/NarratorTransmissionEdgesClient";

export const dynamic = "force-dynamic";

const ENTRY_PREVIEW_CHARS = 6000;

function locationLabel(item: {
  volume_start: number | null;
  page_start: number | null;
  volume_end?: number | null;
  page_end?: number | null;
}): string | null {
  if (item.volume_start === null || item.page_start === null) return null;
  if (
    item.volume_end !== undefined &&
    item.page_end !== undefined &&
    item.volume_end !== null &&
    item.page_end !== null &&
    (item.volume_end !== item.volume_start || item.page_end !== item.page_start)
  ) {
    return `vol. ${item.volume_start}, pp. ${item.page_start}-${item.page_end}`;
  }
  return `vol. ${item.volume_start}, p. ${item.page_start}`;
}

function entryPreview(entry: RijalEntryRead): string {
  if (entry.text_raw.length <= ENTRY_PREVIEW_CHARS) return entry.text_raw;
  return `${entry.text_raw.slice(0, ENTRY_PREVIEW_CHARS)}\n\n[Entry preview truncated in the UI. Open the source link for the full text.]`;
}

export default async function NarratorPage({
  params,
}: {
  params: Promise<{ narratorId: string }>;
}) {
  const { narratorId } = await params;
  const id = Number(narratorId);
  if (!Number.isFinite(id)) notFound();

  const narrator = await getNarrator(id);
  if (!narrator) notFound();
  const aliases = narrator.aliases ?? [];
  const statements = narrator.statements ?? [];
  const rijalEntries = narrator.rijal_entries ?? [];
  const occurrences = narrator.occurrences ?? [];
  const appearanceCounts = narrator.appearance_counts ?? [];
  const appearances = narrator.appearances ?? [];
  const appearancesTotal = narrator.appearances_total ?? appearances.length;
  const occurrencesTotal = narrator.occurrences_total ?? occurrences.length;
  const initialTransmissionSourceBookId =
    appearanceCounts.find((count) => count.source_book_id === "11005")?.source_book_id ??
    appearanceCounts[0]?.source_book_id ??
    null;
  const transmissionEdges = await getNarratorTransmissionEdges(narrator.id, {
    sourceBookId: initialTransmissionSourceBookId ?? undefined,
    limit: 25,
    sampleLimit: 3,
  });

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link href="/books" className="inline-flex min-h-11 items-center text-sm font-medium text-accent hover:underline">
          Back to library
        </Link>
        <Link
          href={`/graph?narrator=${narrator.id}`}
          className="inline-flex min-h-11 items-center text-sm font-medium text-accent hover:underline"
        >
          View in the network →
        </Link>
      </div>

      <header className="mt-5 border-b border-border pb-5">
        <p className="text-xs tracking-wide text-muted/70 uppercase">Narrator profile</p>
        <h1 dir="rtl" lang="ar" className={`${amiri.className} mt-2 text-right text-4xl font-semibold text-foreground sm:text-5xl`}>
          {formatArabicText(narrator.canonical_name_ar)}
        </h1>
        <div className="mt-4 flex flex-wrap gap-2 text-sm text-muted">
          {narrator.kunya ? <span className="rounded-full bg-badge px-3 py-1">{narrator.kunya}</span> : null}
          {narrator.nisba ? <span className="rounded-full bg-badge px-3 py-1">{narrator.nisba}</span> : null}
          {narrator.death_year_note ? (
            <span className="rounded-full bg-badge px-3 py-1">{narrator.death_year_note}</span>
          ) : null}
          {narrator.summary_status ? (
            <span className="rounded-full bg-badge-verified px-3 py-1 text-accent">
              {narrator.summary_status}
            </span>
          ) : null}
        </div>
      </header>

      <section className="mt-6 grid gap-3 sm:grid-cols-4">
        <div className="border-t-2 border-accent bg-surface p-4">
          <p className="text-xs text-muted">Resolved hadiths</p>
          <p className="mt-1 text-2xl font-semibold text-accent">{appearancesTotal}</p>
        </div>
        <div className="border-t-2 border-accent bg-surface p-4">
          <p className="text-xs text-muted">Rijal statements</p>
          <p className="mt-1 text-2xl font-semibold text-accent">{statements.length}</p>
        </div>
        <div className="border-t-2 border-accent bg-surface p-4">
          <p className="text-xs text-muted">Transmission notes</p>
          <p className="mt-1 text-2xl font-semibold text-accent">{occurrencesTotal}</p>
        </div>
        <div className="border-t-2 border-accent bg-surface p-4">
          <p className="text-xs text-muted">Aliases</p>
          <p className="mt-1 text-2xl font-semibold text-accent">{aliases.length}</p>
        </div>
      </section>

      <NarratorTransmissionEdgesClient
        narratorId={narrator.id}
        counts={appearanceCounts}
        initialEdges={transmissionEdges}
        initialSourceBookId={initialTransmissionSourceBookId}
      />

      <NarratorAppearancesClient
        narratorId={narrator.id}
        counts={appearanceCounts}
        initialAppearances={appearances}
        initialTotal={appearancesTotal}
      />

      <section className="mt-8 space-y-4">
        <h2 className="text-sm font-semibold tracking-wide text-muted uppercase">Aliases</h2>
        {aliases.length ? (
          <div dir="rtl" lang="ar" className={`${amiri.className} flex flex-wrap gap-2 text-right`}>
            {aliases.map((alias) => (
              <span key={alias.id} className="rounded-full border border-border px-3 py-1 text-lg">
                {formatArabicText(alias.alias_raw)}
                <span className="ms-2 text-xs text-muted">{alias.alias_type}</span>
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">No aliases have been extracted yet.</p>
        )}
      </section>

      <section className="mt-8 space-y-4">
        <h2 className="text-sm font-semibold tracking-wide text-muted uppercase">Rijal statements</h2>
        {statements.length ? (
          <div className="grid gap-3 lg:grid-cols-2">
            {statements.map((statement) => (
              <div key={statement.id} className="rounded-md border border-border bg-surface p-4">
                <p className="text-xs text-muted">
                  {statement.source_name} / {statement.statement_type} / confidence {statement.confidence}
                </p>
                <p dir="rtl" lang="ar" className={`${amiri.className} mt-2 text-right text-xl leading-loose`}>
                  {formatArabicText(statement.quote_raw)}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">No extracted rijal statements yet.</p>
        )}
      </section>

      <section className="mt-8 space-y-4">
        <h2 className="text-sm font-semibold tracking-wide text-muted uppercase">Mujam entries</h2>
        {rijalEntries.length ? (
          rijalEntries.map((entry) => (
            <details key={entry.id} className="rounded-md border border-border bg-surface">
              <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-3 px-5 py-4">
                <span className="text-sm text-muted">
                  Entry {entry.entry_number ?? "?"}
                  {locationLabel(entry) ? ` / ${locationLabel(entry)}` : ""}
                </span>
                {entry.source_url ? (
                  <a
                    href={entry.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex min-h-11 items-center text-sm font-medium text-accent hover:underline"
                  >
                    Source
                  </a>
                ) : null}
              </summary>
              <div className="border-t border-border px-5 py-4">
                {entry.title_raw ? (
                  <h3 dir="rtl" lang="ar" className={`${amiri.className} text-right text-2xl text-accent`}>
                    {formatArabicText(entry.title_raw)}
                  </h3>
                ) : null}
                <p
                  dir="rtl"
                  lang="ar"
                  className={`${amiri.className} mt-3 whitespace-pre-wrap text-right text-xl leading-loose`}
                >
                  {formatArabicText(entryPreview(entry))}
                </p>
              </div>
            </details>
          ))
        ) : (
          <p className="text-sm text-muted">No Mujam entry is attached to this narrator yet.</p>
        )}
      </section>

      <section className="mt-8 space-y-4">
        <details className="rounded-md border border-border bg-surface">
          <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4">
            <h2 className="text-sm font-semibold tracking-wide text-muted uppercase">Transmission notes</h2>
            <span className="text-xs text-muted">
              showing {occurrences.length} of {occurrencesTotal}
            </span>
          </summary>
          <div className="grid gap-2 border-t border-border p-4 sm:grid-cols-2">
            {occurrences.map((occurrence) => (
              <div key={occurrence.id} className="rounded-md border border-border bg-background p-3">
                <p className="text-xs text-muted">{occurrence.direction}</p>
                <p dir="rtl" lang="ar" className={`${amiri.className} mt-1 text-right text-lg`}>
                  {formatArabicText(occurrence.related_name_raw)}
                </p>
                {occurrence.source_ref_raw ? (
                  <p className="mt-1 text-xs text-muted">{occurrence.source_ref_raw}</p>
                ) : null}
              </div>
            ))}
            {!occurrences.length ? (
              <p className="text-sm text-muted">No transmission occurrence notes yet.</p>
            ) : null}
          </div>
        </details>
      </section>
    </div>
  );
}
