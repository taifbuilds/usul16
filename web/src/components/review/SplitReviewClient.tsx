"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type {
  HadithSplitAudit,
  HadithSplitReviewItem,
  HadithSplitReviewSave,
  HadithSplitReviewStats,
} from "@/lib/api/types";
import { formatArabicText } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type QueueStatus = "all" | "unreviewed" | "approved" | "needs_review" | "rejected";

function labelForFlag(flag: string): string {
  return flag.replaceAll("_", " ");
}

function citation(item: HadithSplitReviewItem): string {
  const h = item.hadith;
  const page =
    h.page_start === h.page_end ? `page ${h.page_start}` : `pages ${h.page_start}-${h.page_end}`;
  return [`vol. ${h.volume_start ?? "?"}`, page, h.printed_number ? `no. ${h.printed_number}` : null]
    .filter(Boolean)
    .join(" / ");
}

async function fetchSplitReviewQueue(params: {
  sourceBookId: string;
  status: QueueStatus;
  flag: string | null;
  limit: number;
}): Promise<HadithSplitReviewItem[]> {
  const query = new URLSearchParams();
  query.set("source_book_id", params.sourceBookId);
  query.set("status", params.status);
  query.set("suspicious_only", "true");
  query.set("limit", String(params.limit));
  if (params.flag) query.set("flag", params.flag);
  const response = await fetch(`${API_BASE_URL}/hadith-split-reviews/queue?${query.toString()}`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json() as Promise<HadithSplitReviewItem[]>;
}

async function saveSplitReview(
  publicId: string,
  payload: HadithSplitReviewSave
): Promise<HadithSplitReviewItem> {
  const response = await fetch(
    `${API_BASE_URL}/hadith-split-reviews/${encodeURIComponent(publicId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") message = body.detail;
    } catch {
      // Keep statusText.
    }
    throw new Error(message);
  }
  return response.json() as Promise<HadithSplitReviewItem>;
}

export function SplitReviewClient({
  initialItems,
  initialStats,
  initialAudit,
  initialFlag,
  sourceBookId,
  queueLimit,
}: {
  initialItems: HadithSplitReviewItem[];
  initialStats: HadithSplitReviewStats;
  initialAudit: HadithSplitAudit;
  initialFlag: string | null;
  sourceBookId: string;
  queueLimit: number;
}) {
  const [items, setItems] = useState(initialItems);
  const [activeFlag, setActiveFlag] = useState<string | null>(initialFlag);
  const [queueStatus, setQueueStatus] = useState<QueueStatus>("unreviewed");
  const [selectedId, setSelectedId] = useState(initialItems[0]?.hadith.public_id ?? "");
  const selected = useMemo(
    () => items.find((item) => item.hadith.public_id === selectedId) ?? items[0] ?? null,
    [items, selectedId]
  );
  const [draftIsnad, setDraftIsnad] = useState(selected?.active_isnad_raw ?? "");
  const [draftMatn, setDraftMatn] = useState(selected?.active_matn_raw ?? "");
  const [status, setStatus] = useState<HadithSplitReviewSave["review_status"]>("approved");
  const [reviewer, setReviewer] = useState("local");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loadingQueue, setLoadingQueue] = useState(false);

  const setEditorFromItem = useCallback((item: HadithSplitReviewItem | null) => {
    setSelectedId(item?.hadith.public_id ?? "");
    setDraftIsnad(item?.active_isnad_raw ?? "");
    setDraftMatn(item?.active_matn_raw ?? "");
    setStatus(
      item?.review?.review_status === "approved" ||
        item?.review?.review_status === "needs_review" ||
        item?.review?.review_status === "rejected"
        ? item.review.review_status
        : "approved"
    );
    setReviewer(item?.review?.reviewer ?? "local");
    setNotes(item?.review?.notes ?? "");
    setMessage(null);
  }, []);

  const loadQueue = useCallback(
    async (flag: string | null = activeFlag, statusValue: QueueStatus = queueStatus) => {
      setLoadingQueue(true);
      setMessage(null);
      try {
        const nextItems = await fetchSplitReviewQueue({
          sourceBookId,
          status: statusValue,
          flag,
          limit: queueLimit,
        });
        setItems(nextItems);
        setActiveFlag(flag);
        setQueueStatus(statusValue);
        setEditorFromItem(nextItems[0] ?? null);
        const url = new URL(window.location.href);
        if (flag) url.searchParams.set("flag", flag);
        else url.searchParams.delete("flag");
        url.searchParams.set("source_book_id", sourceBookId);
        url.searchParams.set("limit", String(queueLimit));
        window.history.replaceState(null, "", url);
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "Could not load queue");
      } finally {
        setLoadingQueue(false);
      }
    },
    [activeFlag, queueLimit, queueStatus, setEditorFromItem, sourceBookId]
  );

  const selectRelative = useCallback(
    (delta: number) => {
      if (!selected || items.length === 0) return;
      const index = items.findIndex((item) => item.hadith.public_id === selected.hadith.public_id);
      const nextIndex = Math.min(Math.max(index + delta, 0), items.length - 1);
      setEditorFromItem(items[nextIndex]);
    },
    [items, selected, setEditorFromItem]
  );

  const saveCurrent = useCallback(
    async (advance: boolean) => {
      if (!selected || !draftMatn.trim()) return;
      setSaving(true);
      setMessage(null);
      try {
        const saved = await saveSplitReview(selected.hadith.public_id, {
          approved_isnad_raw: draftIsnad.trim() || null,
          approved_matn_raw: draftMatn.trim(),
          review_status: status,
          reviewer: reviewer.trim() || null,
          notes: notes.trim() || null,
        });
        const selectedIndex = items.findIndex(
          (item) => item.hadith.public_id === selected.hadith.public_id
        );
        const shouldRemoveFromQueue = queueStatus === "unreviewed";
        const nextItems = shouldRemoveFromQueue
          ? items.filter((item) => item.hadith.public_id !== saved.hadith.public_id)
          : items.map((item) =>
              item.hadith.public_id === saved.hadith.public_id ? saved : item
            );
        setItems(nextItems);
        if (advance || shouldRemoveFromQueue) {
          setEditorFromItem(nextItems[Math.min(selectedIndex, nextItems.length - 1)] ?? null);
        } else {
          setEditorFromItem(saved);
        }
        setMessage(`Saved ${saved.hadith.public_id}`);
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "Save failed");
      } finally {
        setSaving(false);
      }
    },
    [
      draftIsnad,
      draftMatn,
      items,
      notes,
      queueStatus,
      reviewer,
      selected,
      setEditorFromItem,
      status,
    ]
  );

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const command = event.ctrlKey || event.metaKey;
      if (command && event.key.toLowerCase() === "s") {
        event.preventDefault();
        void saveCurrent(false);
      }
      if (command && event.key === "Enter") {
        event.preventDefault();
        void saveCurrent(true);
      }
      if (event.altKey && event.key === "ArrowDown") {
        event.preventDefault();
        selectRelative(1);
      }
      if (event.altKey && event.key === "ArrowUp") {
        event.preventDefault();
        selectRelative(-1);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [saveCurrent, selectRelative]);

  function resetToExtractorDraft() {
    if (!selected) return;
    setDraftIsnad(selected.hadith.isnad_raw ?? "");
    setDraftMatn(selected.hadith.matn_raw);
    setMessage("Reset to extractor draft");
  }

  function splitAtFirstColon() {
    if (!selected) return;
    const text = selected.hadith.full_text_raw;
    const index = text.indexOf(":");
    if (index < 0) {
      setMessage("No colon found in full text");
      return;
    }
    setDraftIsnad(text.slice(0, index + 1).trim());
    setDraftMatn(text.slice(index + 1).trim());
    setMessage("Split at first colon");
  }

  const activeFlagLabel = activeFlag ? labelForFlag(activeFlag) : "all suspicious flags";

  return (
    <div className="grid gap-6 xl:grid-cols-[18rem_20rem_minmax(0,1fr)]">
      <aside className="space-y-4">
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs font-medium tracking-wide text-muted uppercase">Audit snapshot</p>
          <p className="mt-2 text-2xl font-semibold text-accent">
            {initialStats.suspicious_unreviewed}
          </p>
          <p className="text-sm text-muted">suspicious unreviewed hadiths</p>
          <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-muted">
            <span>Total: {initialStats.total_hadiths}</span>
            <span>Flagged: {initialAudit.flagged_hadiths}</span>
            <span>Approved: {initialStats.approved}</span>
            <span>Needs review: {initialStats.needs_review}</span>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-surface p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-muted">Problem buckets</p>
            <button
              type="button"
              onClick={() => void loadQueue(null)}
              className="text-xs font-medium text-accent hover:underline"
            >
              All
            </button>
          </div>
          <div className="max-h-[58vh] space-y-1 overflow-y-auto pr-1">
            {initialAudit.flags.map((bucket) => (
              <button
                key={bucket.flag}
                type="button"
                onClick={() => void loadQueue(bucket.flag)}
                className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                  activeFlag === bucket.flag
                    ? "border-accent bg-badge-verified"
                    : "border-border bg-background hover:border-accent"
                }`}
              >
                <span className="block font-medium">{labelForFlag(bucket.flag)}</span>
                <span className="mt-0.5 block text-xs text-muted">
                  {bucket.unreviewed} unreviewed / {bucket.total} total
                </span>
              </button>
            ))}
          </div>
        </div>
      </aside>

      <aside className="space-y-4">
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-sm font-medium text-muted">Queue</p>
          <p className="mt-1 text-xs text-muted">
            Showing {items.length} for {activeFlagLabel}
          </p>
          <div className="mt-3 flex gap-2">
            <select
              value={queueStatus}
              onChange={(event) => void loadQueue(activeFlag, event.target.value as QueueStatus)}
              className="min-w-0 flex-1 rounded-lg border border-border bg-background px-2 py-2 text-sm outline-none focus:border-accent"
            >
              <option value="unreviewed">Unreviewed</option>
              <option value="needs_review">Needs review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="all">All</option>
            </select>
            <button
              type="button"
              onClick={() => void loadQueue()}
              className="rounded-lg border border-border px-3 py-2 text-sm font-medium text-accent hover:border-accent"
            >
              {loadingQueue ? "..." : "Reload"}
            </button>
          </div>
        </div>

        <div className="max-h-[70vh] space-y-2 overflow-y-auto pr-1">
          {items.map((item) => {
            const isSelected = item.hadith.public_id === selected?.hadith.public_id;
            return (
              <button
                key={item.hadith.id}
                type="button"
                onClick={() => setEditorFromItem(item)}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  isSelected
                    ? "border-accent bg-badge-verified"
                    : "border-border bg-surface hover:border-accent"
                }`}
              >
                <span className="font-mono text-sm text-accent">{item.hadith.public_id}</span>
                <span className="mt-1 block text-xs text-muted">{citation(item)}</span>
                <span className="mt-2 flex flex-wrap gap-1">
                  {item.suspicion_flags.slice(0, 3).map((flag) => (
                    <span key={flag} className="rounded-full bg-badge px-2 py-0.5 text-[11px]">
                      {labelForFlag(flag)}
                    </span>
                  ))}
                </span>
              </button>
            );
          })}
          {!items.length ? (
            <div className="rounded-lg border border-border bg-surface p-4 text-sm text-muted">
              No rows in this queue.
            </div>
          ) : null}
        </div>
      </aside>

      <section className="min-w-0 space-y-5">
        {!selected ? (
          <div className="rounded-lg border border-border bg-surface p-6">
            <p className="font-medium">No hadith selected.</p>
            <p className="mt-1 text-sm text-muted">Choose another bucket or reload the queue.</p>
          </div>
        ) : (
          <>
            <div className="rounded-lg border border-border bg-surface p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-mono text-sm text-accent">{selected.hadith.public_id}</p>
                  <p className="text-sm text-muted">{citation(selected)}</p>
                </div>
                <div className="flex flex-wrap gap-3 text-sm">
                  <Link
                    href={`/hadith/${encodeURIComponent(selected.hadith.public_id)}`}
                    className="font-medium text-accent hover:underline"
                  >
                    Public card
                  </Link>
                  <a
                    href={selected.hadith.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted hover:text-accent hover:underline"
                  >
                    Source page
                  </a>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {selected.suspicion_flags.map((flag) => (
                  <button
                    key={flag}
                    type="button"
                    onClick={() => void loadQueue(flag)}
                    className="rounded-full bg-badge px-2.5 py-1 text-xs text-muted hover:text-accent"
                  >
                    {labelForFlag(flag)}
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-border bg-surface p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm font-medium text-muted">Full raw hadith</p>
                <div className="flex flex-wrap gap-2 text-xs">
                  <button
                    type="button"
                    onClick={splitAtFirstColon}
                    className="rounded-lg border border-border px-2.5 py-1 text-accent hover:border-accent"
                  >
                    Split at first colon
                  </button>
                  <button
                    type="button"
                    onClick={resetToExtractorDraft}
                    className="rounded-lg border border-border px-2.5 py-1 text-muted hover:border-accent hover:text-accent"
                  >
                    Reset to draft
                  </button>
                  <button
                    type="button"
                    onClick={() => setDraftIsnad("")}
                    className="rounded-lg border border-border px-2.5 py-1 text-muted hover:border-accent hover:text-accent"
                  >
                    Clear isnad
                  </button>
                </div>
              </div>
              <p
                dir="rtl"
                lang="ar"
                className={`${amiri.className} mt-3 max-h-72 overflow-y-auto whitespace-pre-wrap text-right text-xl leading-loose`}
              >
                {formatArabicText(selected.hadith.full_text_raw)}
              </p>
            </div>

            <div className="grid gap-5 xl:grid-cols-2">
              <label className="block rounded-lg border border-border bg-surface p-4">
                <span className="text-sm font-medium text-muted">Approved isnad</span>
                <textarea
                  dir="rtl"
                  lang="ar"
                  value={draftIsnad}
                  onChange={(event) => setDraftIsnad(event.target.value)}
                  className={`${amiri.className} mt-3 h-72 w-full resize-y rounded-lg border border-border bg-background p-3 text-right text-xl leading-loose outline-none focus:border-accent`}
                />
              </label>

              <label className="block rounded-lg border border-border bg-surface p-4">
                <span className="text-sm font-medium text-muted">Approved matn</span>
                <textarea
                  dir="rtl"
                  lang="ar"
                  value={draftMatn}
                  onChange={(event) => setDraftMatn(event.target.value)}
                  className={`${amiri.className} mt-3 h-72 w-full resize-y rounded-lg border border-border bg-background p-3 text-right text-xl leading-loose outline-none focus:border-accent`}
                />
              </label>
            </div>

            <div className="rounded-lg border border-border bg-surface p-4">
              <div className="grid gap-4 sm:grid-cols-[12rem_12rem_minmax(0,1fr)]">
                <label className="block text-sm">
                  <span className="font-medium text-muted">Status</span>
                  <select
                    value={status}
                    onChange={(event) =>
                      setStatus(event.target.value as HadithSplitReviewSave["review_status"])
                    }
                    className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-accent"
                  >
                    <option value="approved">Approved</option>
                    <option value="needs_review">Needs review</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </label>
                <label className="block text-sm">
                  <span className="font-medium text-muted">Reviewer</span>
                  <input
                    value={reviewer}
                    onChange={(event) => setReviewer(event.target.value)}
                    className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-accent"
                  />
                </label>
                <label className="block text-sm">
                  <span className="font-medium text-muted">Notes</span>
                  <input
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                    className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-accent"
                  />
                </label>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => void saveCurrent(false)}
                  disabled={saving || !draftMatn.trim()}
                  className="rounded-lg border border-accent px-4 py-2 text-sm font-medium text-accent disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save"}
                </button>
                <button
                  type="button"
                  onClick={() => void saveCurrent(true)}
                  disabled={saving || !draftMatn.trim()}
                  className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-accent-foreground disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Save + next
                </button>
                <button
                  type="button"
                  onClick={() => selectRelative(-1)}
                  className="rounded-lg border border-border px-3 py-2 text-sm text-muted hover:border-accent hover:text-accent"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => selectRelative(1)}
                  className="rounded-lg border border-border px-3 py-2 text-sm text-muted hover:border-accent hover:text-accent"
                >
                  Next
                </button>
                <p className="text-xs text-muted">
                  Ctrl+S save / Ctrl+Enter save+next / Alt+Up/Down move
                </p>
                {message ? <p className="basis-full text-sm text-muted">{message}</p> : null}
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
