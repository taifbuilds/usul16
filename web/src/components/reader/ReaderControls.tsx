"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
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
  const [readerSize, setReaderSize] = useState<"compact" | "comfortable" | "large">("comfortable");

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      const stored = window.localStorage.getItem("usul16-reader-size");
      if (stored === "compact" || stored === "comfortable" || stored === "large") {
        setReaderSize(stored);
        document.documentElement.setAttribute("data-reader-size", stored);
      }
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

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

  function changeReaderSize(size: "compact" | "comfortable" | "large") {
    setReaderSize(size);
    document.documentElement.setAttribute("data-reader-size", size);
    window.localStorage.setItem("usul16-reader-size", size);
  }

  const volumeOptions = Array.from({ length: Math.max(volumeCount, volumeNumber) }, (_, i) => i + 1);
  const navButton =
    "flex h-11 w-11 items-center justify-center rounded-md border border-border bg-background text-base transition hover:border-accent hover:text-accent disabled:opacity-40 disabled:hover:border-border disabled:hover:text-foreground";

  return (
    <div className="text-sm">
      <div className="flex items-center justify-between gap-2 sm:gap-3">
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

        <div className="flex min-w-0 items-center gap-1.5 sm:gap-2">
        <select
          value={volumeNumber}
          aria-label="Volume"
          onChange={(event) => goTo(Number(event.target.value), 1)}
          className="min-h-11 min-w-0 rounded-md border border-border bg-background px-2 py-2 sm:px-3"
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
            className="min-h-11 w-16 rounded-md border border-border bg-background px-3 py-2 text-center"
          />
          <span className="whitespace-nowrap text-muted">/ {lastPage}</span>
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

      <div className="mt-3 flex flex-wrap items-center justify-end gap-2 border-t border-border pt-3">
        <span className="me-auto text-xs text-muted">Arabic text size</span>
        {([
          ["compact", "A−", "Compact Arabic text"],
          ["comfortable", "A", "Comfortable Arabic text"],
          ["large", "A+", "Large Arabic text"],
        ] as const).map(([size, label, ariaLabel]) => (
          <button
            key={size}
            type="button"
            aria-label={ariaLabel}
            aria-pressed={readerSize === size}
            onClick={() => changeReaderSize(size)}
            className={`min-h-11 min-w-11 rounded-md border px-2 py-1.5 font-serif transition-colors ${
              readerSize === size
                ? "border-accent bg-accent text-accent-foreground"
                : "border-border bg-background text-foreground hover:border-accent"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
