"use client";

import { useEffect, useRef, useState } from "react";
import {
  SHARE_LANGUAGES,
  availableLanguages,
  type ShareCard,
  type ShareLanguage,
} from "@/lib/share/card";
import {
  SHARE_FORMATS,
  canvasToBlob,
  ensureFonts,
  readFonts,
  readTheme,
  renderShareImage,
  shareFileName,
  type ShareFormat,
} from "@/lib/share/render";

// Preview and export. A native <dialog> because this is a focused sub-task
// with its own controls — it gets the modal focus trap and Escape handling for
// free, and nothing behind it stays interactive while a render is in flight.

interface Preview {
  url: string;
  blob: Blob;
  truncated: boolean;
}

const PREVIEW_TIMEOUT_MS = 6_000;

async function within<T>(task: Promise<T>, timeoutMs: number): Promise<T> {
  let timeoutId: number | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timeoutId = window.setTimeout(
      () => reject(new Error("Image preparation timed out")),
      timeoutMs
    );
  });
  try {
    return await Promise.race([task, timeout]);
  } finally {
    if (timeoutId !== undefined) window.clearTimeout(timeoutId);
  }
}

export function RepostDialog({
  card,
  open,
  onClose,
  onPrepared,
  onPreparationError,
}: {
  card: ShareCard;
  open: boolean;
  onClose: () => void;
  onPrepared?: () => void;
  onPreparationError?: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const previewUrlRef = useRef<string | null>(null);
  const languages = availableLanguages(card);
  const [language, setLanguage] = useState<ShareLanguage>(languages.includes("both") ? "both" : "ar");
  const [format, setFormat] = useState<ShareFormat>("portrait");
  const [saved, setSaved] = useState(false);
  // Re-render the preview when the reader flips the theme behind the dialog.
  const [themeTick, setThemeTick] = useState(0);
  const [canShareFile, setCanShareFile] = useState(false);

  // One key describes what the preview *should* show. Holding it alongside
  // each result makes "still rendering" a derived fact rather than a flag that
  // can fall out of step with the work in flight.
  const wanted = `${language}|${format}|${themeTick}`;
  const [preview, setPreview] = useState<{ key: string; value: Preview } | null>(null);
  const [error, setError] = useState<{ key: string; message: string } | null>(null);
  const busy = open && preview?.key !== wanted && error?.key !== wanted;
  const ready = preview?.key === wanted;
  const shown = preview?.value ?? null;
  const selectedFormat = SHARE_FORMATS.find((option) => option.value === format);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    // Rendering starts as soon as the reader asks for an image, but the modal
    // stays out of the way until there is a real preview to show. If an option
    // changes while the dialog is already open, keep it open during that
    // smaller refresh instead of making the surface flash in and out.
    if (open) {
      if (ready && !dialog.open) dialog.showModal();
      return;
    }
    if (dialog.open) dialog.close();
  }, [open, ready]);

  useEffect(() => {
    if (open && ready) onPrepared?.();
  }, [onPrepared, open, ready]);

  useEffect(() => {
    const observer = new MutationObserver(() => setThemeTick((tick) => tick + 1));
    observer.observe(document.documentElement, { attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!open || ready) return;
    let cancelled = false;

    (async () => {
      // Every state update below sits behind an await, so opening the dialog
      // does not cascade renders before the first frame.
      try {
        setError(null);
        const prepared = await within(
          (async () => {
            const fonts = readFonts();
            await ensureFonts(fonts);
            const { canvas, truncated } = renderShareImage({
              card,
              language,
              format,
              theme: readTheme(),
              fonts,
            });
            const blob = await canvasToBlob(canvas);
            return { blob, truncated };
          })(),
          PREVIEW_TIMEOUT_MS
        );
        if (cancelled) return;
        if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
        const url = URL.createObjectURL(prepared.blob);
        previewUrlRef.current = url;
        setPreview({
          key: wanted,
          value: { url, blob: prepared.blob, truncated: prepared.truncated },
        });
        setCanShareFile(
          typeof navigator.canShare === "function" &&
            navigator.canShare({
              files: [
                new File([prepared.blob], shareFileName(card, format), { type: "image/png" }),
              ],
            })
        );
      } catch (cause) {
        if (cancelled) return;
        await Promise.resolve();
        setError({
          key: wanted,
          message: cause instanceof Error ? cause.message : "Could not render the image",
        });
        onPreparationError?.();
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [open, ready, card, language, format, onPreparationError, wanted]);

  useEffect(
    () => () => {
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    },
    []
  );

  useEffect(() => {
    if (!saved) return;
    const timer = window.setTimeout(() => setSaved(false), 2200);
    return () => window.clearTimeout(timer);
  }, [saved]);

  function download() {
    if (!shown) return;
    const link = document.createElement("a");
    link.href = shown.url;
    link.download = shareFileName(card, format);
    link.click();
    setSaved(true);
  }

  function requestClose() {
    const dialog = dialogRef.current;
    if (dialog?.open) dialog.close();
    else onClose();
  }

  async function shareImage() {
    if (!shown) return;
    const file = new File([shown.blob], shareFileName(card, format), { type: "image/png" });
    try {
      await navigator.share({ files: [file], text: card.url });
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return;
      download();
    }
  }

  // Name the levers that would actually fit more of this narration, rather
  // than reporting the constraint and leaving the reader to guess.
  const fitOptions = [
    format !== "story" ? "a taller size" : null,
    language === "both" ? "a single language" : null,
  ].filter(Boolean);
  const fitHint = fitOptions.length ? `Try ${fitOptions.join(" or ")}.` : "";

  return (
    <dialog
      ref={dialogRef}
      dir="ltr"
      onClose={onClose}
      onCancel={(event) => {
        event.preventDefault();
        requestClose();
      }}
      onClick={(event) => {
        // Clicking the backdrop lands on the dialog element itself.
        if (event.target === dialogRef.current) requestClose();
      }}
      aria-labelledby="repost-title"
      className="repost-dialog m-auto flex max-h-[calc(100dvh-2rem)] w-[min(46rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl border border-border bg-surface p-0 font-sans text-foreground shadow-2xl backdrop:bg-[color:var(--shadow-color)] backdrop:backdrop-blur-sm"
    >
      <div className="flex shrink-0 items-start justify-between gap-4 border-b border-border px-5 py-4">
        <div>
          <h2 id="repost-title" className="text-base font-semibold">
            Share hadith image
          </h2>
          <p className="mt-0.5 text-xs text-muted">
            Includes the collection, printed page, and a link back to the record.
          </p>
        </div>
        <button
          type="button"
          onClick={requestClose}
          aria-label="Close"
          className="-mr-1 -mt-1 inline-flex min-h-11 min-w-11 items-center justify-center rounded-md text-muted transition-colors hover:bg-surface-2 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          <svg viewBox="0 0 16 16" aria-hidden className="size-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <path d="M4 4l8 8M12 4l-8 8" />
          </svg>
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="grid gap-5 p-5 md:grid-cols-[minmax(0,1fr)_13rem]">
        <div
          aria-busy={busy}
          className="flex min-h-[15rem] items-center justify-center rounded-lg bg-background p-3 md:min-h-[30rem]"
        >
          {error && error.key === wanted ? (
            <p className="max-w-xs text-center text-sm text-muted">{error.message}</p>
          ) : shown ? (
            // A blob URL from a canvas render: next/image cannot optimise it,
            // and the bytes are already in memory.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={shown.url}
              alt={`Preview of the shareable image for ${card.publicId}`}
              className={`max-h-[19rem] w-auto max-w-full rounded-sm shadow-md transition-opacity duration-200 sm:max-h-[36rem] ${
                busy ? "opacity-40" : "opacity-100"
              }`}
            />
          ) : (
            <div className="text-center" role="status" aria-live="polite">
              <div
                aria-hidden
                className="mx-auto h-56 w-44 animate-pulse rounded-sm bg-surface-2 md:h-[30rem] md:w-[24rem]"
              />
              <p className="mt-3 text-xs text-muted">Preparing image…</p>
            </div>
          )}
        </div>

        <details className="self-start rounded-md border border-border bg-background">
          <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-2 px-3 text-sm font-medium text-foreground marker:content-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40">
            <span className="whitespace-nowrap">Options</span>
            <span className="text-xs font-normal text-muted">
              {selectedFormat?.label}
            </span>
          </summary>
          <div className="space-y-3 border-t border-border p-3">
          {languages.length > 1 ? (
            <label className="grid gap-1.5 text-xs font-medium text-foreground">
              Text
              <select
                value={language}
                onChange={(event) => setLanguage(event.target.value as ShareLanguage)}
                className="min-h-10 rounded-md border border-border bg-surface px-2 text-sm font-normal text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40"
              >
                {SHARE_LANGUAGES.filter((option) => languages.includes(option.value)).map(
                  (option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  )
                )}
              </select>
            </label>
          ) : (
            <p className="text-xs leading-relaxed text-muted">
              Arabic only. No published English translation is attached to this record.
            </p>
          )}

          <label className="grid gap-1.5 text-xs font-medium text-foreground">
            Image size
            <select
              value={format}
              onChange={(event) => setFormat(event.target.value as ShareFormat)}
              className="min-h-10 rounded-md border border-border bg-surface px-2 text-sm font-normal text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40"
            >
              {SHARE_FORMATS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label} — {option.hint}
                </option>
              ))}
            </select>
          </label>

          {shown?.truncated ? (
            <p className="text-left text-xs leading-relaxed text-gold">
              The image uses an opening excerpt and links to the full narration. {fitHint}
            </p>
          ) : null}

          </div>
        </details>
        </div>
      </div>

      <div className="flex shrink-0 items-center justify-between gap-3 border-t border-border px-5 py-4">
        <button
          type="button"
          onClick={requestClose}
          className="min-h-11 rounded-md px-4 text-sm font-semibold text-foreground transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          Close
        </button>
        <button
          type="button"
          onClick={canShareFile ? shareImage : download}
          disabled={!shown || busy}
          className="min-h-11 rounded-md bg-accent px-5 text-sm font-semibold text-accent-foreground transition-colors hover:bg-accent-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:opacity-50"
        >
          {saved
            ? "Image saved"
            : busy
              ? "Preparing image…"
              : canShareFile
                ? "Share image"
                : "Download image"}
        </button>
      </div>
    </dialog>
  );
}
