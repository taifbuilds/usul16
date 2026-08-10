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

export function RepostDialog({
  card,
  open,
  onClose,
}: {
  card: ShareCard;
  open: boolean;
  onClose: () => void;
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
  const shown = preview?.value ?? null;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  useEffect(() => {
    const observer = new MutationObserver(() => setThemeTick((tick) => tick + 1));
    observer.observe(document.documentElement, { attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;

    (async () => {
      // Every state update below sits behind an await, so opening the dialog
      // does not cascade renders before the first frame.
      try {
        const fonts = readFonts();
        await ensureFonts(fonts);
        if (cancelled) return;
        const { canvas, truncated } = renderShareImage({
          card,
          language,
          format,
          theme: readTheme(),
          fonts,
        });
        const blob = await canvasToBlob(canvas);
        if (cancelled) return;
        if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
        const url = URL.createObjectURL(blob);
        previewUrlRef.current = url;
        setPreview({ key: wanted, value: { url, blob, truncated } });
        setCanShareFile(
          typeof navigator.canShare === "function" &&
            navigator.canShare({
              files: [new File([blob], shareFileName(card, format), { type: "image/png" })],
            })
        );
      } catch (cause) {
        if (cancelled) return;
        await Promise.resolve();
        setError({
          key: wanted,
          message: cause instanceof Error ? cause.message : "Could not render the image",
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [open, card, language, format, wanted]);

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

  const segment = (active: boolean) =>
    `min-h-9 rounded-md px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 ${
      active
        ? "bg-accent text-accent-foreground"
        : "border border-border text-muted hover:border-border-strong hover:text-foreground"
    }`;

  return (
    <dialog
      ref={dialogRef}
      dir="ltr"
      onClose={onClose}
      onCancel={onClose}
      onClick={(event) => {
        // Clicking the backdrop lands on the dialog element itself.
        if (event.target === dialogRef.current) onClose();
      }}
      aria-labelledby="repost-title"
      className="repost-dialog m-auto flex max-h-[calc(100dvh-2rem)] w-[min(46rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl border border-border bg-surface p-0 font-sans text-foreground shadow-2xl backdrop:bg-[color:var(--shadow-color)] backdrop:backdrop-blur-sm"
    >
      <div className="flex shrink-0 items-start justify-between gap-4 border-b border-border px-5 py-4">
        <div>
          <h2 id="repost-title" className="text-base font-semibold">
            Repost this hadith
          </h2>
          <p className="mt-0.5 text-xs text-muted">
            The image carries its collection, printed page and permalink, so it stays traceable
            wherever it travels.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="-mr-1 -mt-1 rounded-md p-2 text-muted transition-colors hover:bg-surface-2 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          <svg viewBox="0 0 16 16" aria-hidden className="size-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <path d="M4 4l8 8M12 4l-8 8" />
          </svg>
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="grid gap-5 p-5 sm:grid-cols-[minmax(0,1fr)_14.5rem]">
        <div className="flex min-h-[15rem] items-center justify-center rounded-lg bg-background p-3 sm:min-h-[32rem]">
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
            <div
              aria-hidden
              className="h-56 w-44 animate-pulse rounded-sm bg-surface-2 sm:h-[34rem] sm:w-[27rem]"
            />
          )}
        </div>

        <div className="flex flex-col gap-5">
          {languages.length > 1 ? (
            <fieldset>
              <legend className="mb-2 text-xs font-semibold text-foreground">Text</legend>
              <div className="flex flex-wrap gap-1.5">
                {SHARE_LANGUAGES.filter((option) => languages.includes(option.value)).map(
                  (option) => (
                    <button
                      key={option.value}
                      type="button"
                      aria-pressed={language === option.value}
                      onClick={() => setLanguage(option.value)}
                      className={segment(language === option.value)}
                    >
                      {option.label}
                    </button>
                  )
                )}
              </div>
            </fieldset>
          ) : (
            <p className="text-xs leading-relaxed text-muted">
              Arabic only — no published English translation is attached to this record yet.
            </p>
          )}

          <fieldset>
            <legend className="mb-2 text-xs font-semibold text-foreground">Size</legend>
            <div className="flex flex-col gap-1.5">
              {SHARE_FORMATS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  aria-pressed={format === option.value}
                  onClick={() => setFormat(option.value)}
                  className={`flex items-center justify-between ${segment(format === option.value)}`}
                >
                  <span>{option.label}</span>
                  <span className={format === option.value ? "opacity-80" : "text-muted"}>
                    {option.hint}
                  </span>
                </button>
              ))}
            </div>
          </fieldset>

          {shown?.truncated ? (
            <p className="border-t border-border pt-3 text-left text-xs leading-relaxed text-gold">
              Too long to set legibly here, so the image shows its opening and links to the rest.
              {fitHint ? ` ${fitHint}` : ""}
            </p>
          ) : null}

        </div>
        </div>
      </div>

      <div className="flex shrink-0 flex-col-reverse gap-2 border-t border-border px-5 py-4 sm:flex-row sm:justify-end">
        <button
          type="button"
          onClick={download}
          disabled={!shown || busy}
          className={`min-h-11 rounded-md px-5 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:opacity-50 ${
            canShareFile
              ? "border border-border text-foreground hover:bg-surface-2"
              : "bg-accent text-accent-foreground hover:bg-accent-strong"
          }`}
        >
          {saved ? "Saved" : busy ? "Rendering…" : "Download PNG"}
        </button>
        {canShareFile ? (
          <button
            type="button"
            onClick={shareImage}
            disabled={!shown || busy}
            className="min-h-11 rounded-md bg-accent px-5 text-sm font-semibold text-accent-foreground transition-colors hover:bg-accent-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 disabled:opacity-50"
          >
            Share image
          </button>
        ) : null}
      </div>
    </dialog>
  );
}
