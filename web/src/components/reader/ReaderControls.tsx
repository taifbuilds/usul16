"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

export function ReaderControls({
  bookId,
  volumeNumber,
  pageNumber,
  volumeCount,
  availablePages,
}: {
  bookId: number;
  volumeNumber: number;
  pageNumber: number;
  volumeCount: number;
  availablePages: number[];
}) {
  const router = useRouter();
  const [pageInput, setPageInput] = useState(String(pageNumber));

  const pages = useMemo(
    () => [...new Set(availablePages)].sort((a, b) => a - b),
    [availablePages]
  );
  const index = pages.indexOf(pageNumber);
  const prevPage = index > 0 ? pages[index - 1] : null;
  const nextPage = index >= 0 && index < pages.length - 1 ? pages[index + 1] : null;
  const lastPage = pages[pages.length - 1] ?? pageNumber;

  function goTo(volume: number, page: number) {
    router.push(`/read/${bookId}/${volume}/${page}`);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const requested = Math.trunc(Number(pageInput));
    if (!Number.isFinite(requested)) return;
    // Snap to the nearest page that actually exists in this volume.
    const target = pages.reduce(
      (best, candidate) => (Math.abs(candidate - requested) < Math.abs(best - requested) ? candidate : best),
      pages[0] ?? requested
    );
    goTo(volumeNumber, target);
  }

  const volumeOptions = Array.from({ length: Math.max(volumeCount, volumeNumber) }, (_, i) => i + 1);
  const navButton =
    "flex h-9 w-9 items-center justify-center rounded-full border border-border bg-surface text-base transition hover:border-accent hover:text-accent disabled:opacity-40 disabled:hover:border-border disabled:hover:text-foreground";

  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      {/* RTL book: "previous page" sits on the right, so use the right arrow */}
      <button
        type="button"
        aria-label="Next page"
        onClick={() => nextPage !== null && goTo(volumeNumber, nextPage)}
        disabled={nextPage === null}
        className={navButton}
      >
        ←
      </button>

      <div className="flex items-center gap-2">
        <select
          value={volumeNumber}
          aria-label="Volume"
          onChange={(event) => goTo(Number(event.target.value), 1)}
          className="rounded-full border border-border bg-surface px-3 py-1.5"
        >
          {volumeOptions.map((volume) => (
            <option key={volume} value={volume}>
              Vol. {volume}
            </option>
          ))}
        </select>

        <form onSubmit={handleSubmit} className="flex items-center gap-1.5">
          <input
            type="number"
            aria-label="Page number"
            value={pageInput}
            onChange={(event) => setPageInput(event.target.value)}
            className="w-16 rounded-full border border-border bg-surface px-3 py-1.5 text-center"
          />
          <span className="text-muted">/ {lastPage}</span>
        </form>
      </div>

      <button
        type="button"
        aria-label="Previous page"
        onClick={() => prevPage !== null && goTo(volumeNumber, prevPage)}
        disabled={prevPage === null}
        className={navButton}
      >
        →
      </button>
    </div>
  );
}
