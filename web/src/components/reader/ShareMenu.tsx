"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import type { HadithRead } from "@/lib/api/types";
import { buildShareCard, shareText, type ShareCard } from "@/lib/share/card";
import { RepostDialog } from "@/components/reader/RepostDialog";

// The record's share affordance. Three actions in rising commitment: take the
// words, take the address, or publish a rendered folio of it.
//
// The popover uses the native top-layer API on purpose — the hadith card is
// `overflow-hidden`, so an absolutely positioned menu inside it would be
// clipped at the card edge.

type Feedback = { action: string; message: string } | null;

function ShareIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden className="size-3.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 10.5V2m0 0L5.25 4.75M8 2l2.75 2.75" />
      <path d="M3.5 8.5v4a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1v-4" />
    </svg>
  );
}

export function ShareMenu({
  hadith,
  bookTitle = null,
  className = "",
}: {
  hadith: HadithRead;
  bookTitle?: string | null;
  className?: string;
}) {
  const popoverId = useId().replace(/:/g, "");
  const buttonRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [card, setCard] = useState<ShareCard | null>(null);
  const [feedback, setFeedback] = useState<Feedback>(null);
  const [repostOpen, setRepostOpen] = useState(false);
  const [canNativeShare, setCanNativeShare] = useState(false);

  // Built on first open, not on mount: the permalink needs
  // `window.location.origin`, which would differ between the server and client
  // renders, and a page of forty hadiths should not compose forty share cards
  // nobody asked for.
  const ensureCard = useCallback((): ShareCard => {
    const built = card ?? buildShareCard(hadith, bookTitle, window.location.origin);
    if (!card) setCard(built);
    setCanNativeShare(typeof navigator.share === "function");
    return built;
  }, [card, hadith, bookTitle]);

  useEffect(() => {
    if (!feedback) return;
    const timer = window.setTimeout(() => setFeedback(null), 2000);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  /** Anchor the top-layer popover under the button, kept inside the viewport. */
  const position = useCallback(() => {
    const button = buttonRef.current;
    const popover = popoverRef.current;
    if (!button || !popover) return;
    const anchor = button.getBoundingClientRect();
    const width = popover.offsetWidth;
    const left = Math.min(
      Math.max(8, anchor.right - width),
      Math.max(8, window.innerWidth - width - 8)
    );
    const below = anchor.bottom + 8;
    const flip = below + popover.offsetHeight > window.innerHeight - 8;
    popover.style.left = `${left}px`;
    popover.style.top = flip
      ? `${Math.max(8, anchor.top - popover.offsetHeight - 8)}px`
      : `${below}px`;
  }, []);

  const close = useCallback(() => {
    popoverRef.current?.hidePopover?.();
  }, []);

  async function copy(action: string, value: string, message: string) {
    try {
      await navigator.clipboard.writeText(value);
      setFeedback({ action, message });
    } catch {
      setFeedback({ action, message: "Clipboard blocked — select the text instead" });
    }
  }

  async function handleCopyText() {
    const current = ensureCard();
    await copy("text", shareText(current, current.english ? "both" : "ar"), "Hadith copied");
    close();
  }

  async function handleLink() {
    const current = ensureCard();
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title: current.bookTitle ?? "Usul16", url: current.url });
        close();
        return;
      } catch (error) {
        // An abort is the reader closing the sheet; anything else falls back.
        if (error instanceof DOMException && error.name === "AbortError") return;
      }
    }
    await copy("link", current.url, "Link copied");
    close();
  }

  const itemClass =
    "flex w-full items-center justify-between gap-6 px-3.5 py-2.5 text-left text-sm text-foreground transition-colors hover:bg-surface-2 focus-visible:bg-surface-2 focus-visible:outline-none disabled:opacity-50";

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        popoverTarget={popoverId}
        onClick={() => {
          ensureCard();
          window.requestAnimationFrame(position);
        }}
        className={`inline-flex min-h-8 items-center gap-1.5 rounded-md px-2 py-1 font-sans text-xs font-medium text-muted transition-colors hover:bg-surface-2 hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 ${className}`}
      >
        <ShareIcon />
        {/* The label doubles as the confirmation, so announce the swap rather
            than leaving screen-reader users with silent success. */}
        <span aria-live="polite">{feedback ? feedback.message : "Share"}</span>
      </button>

      <div
        ref={popoverRef}
        id={popoverId}
        popover="auto"
        dir="ltr"
        onToggle={(event: React.ToggleEvent<HTMLDivElement>) => {
          if (event.newState === "open") position();
        }}
        className="share-popover m-0 w-64 overflow-hidden rounded-lg border border-border bg-surface p-0 font-sans text-foreground shadow-lg backdrop:bg-transparent"
      >
        <div className="py-1.5">
          <button type="button" onClick={handleCopyText} disabled={!card} className={itemClass}>
            <span>Copy hadith text</span>
            <span className="text-xs text-muted">
              {card?.english ? "ع + EN" : "ع"}
            </span>
          </button>
          <button type="button" onClick={handleLink} disabled={!card} className={itemClass}>
            <span>{canNativeShare ? "Share link" : "Copy link"}</span>
            <span className="font-mono text-xs text-muted">/hadith</span>
          </button>
        </div>
        <div className="border-t border-border py-1.5">
          <button
            type="button"
            disabled={!card}
            onClick={() => {
              close();
              setRepostOpen(true);
            }}
            className={itemClass}
          >
            <span className="font-medium text-accent">Repost as image</span>
            <span aria-hidden className="text-accent">
              →
            </span>
          </button>
          <p className="px-3.5 pt-0.5 pb-1 text-xs leading-snug text-muted">
            A rendered folio with its source and permalink.
          </p>
        </div>
      </div>

      {card ? (
        <RepostDialog card={card} open={repostOpen} onClose={() => setRepostOpen(false)} />
      ) : null}
    </>
  );
}
