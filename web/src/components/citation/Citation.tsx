"use client";

import { useState } from "react";
import { amiri } from "@/lib/fonts";
import { formatCitation } from "@/lib/citation";

export function Citation({
  title,
  volumeNumber,
  pageNumber,
  sourceUrl,
  pageEnd = null,
  printedNumber = null,
  publicId = null,
  permanentPath = null,
}: {
  title: string;
  volumeNumber: number | null;
  pageNumber: number;
  sourceUrl: string;
  pageEnd?: number | null;
  printedNumber?: string | null;
  publicId?: string | null;
  permanentPath?: string | null;
}) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);

  async function handleCopy() {
    const canonicalUrl = permanentPath ? new URL(permanentPath, window.location.origin).toString() : window.location.href;
    const accessedOn = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" }).format(new Date());
    try {
      await navigator.clipboard.writeText(formatCitation({ title, volumeNumber, pageNumber, pageEnd, printedNumber, publicId, canonicalUrl, sourceUrl, accessedOn }));
      setCopyError(false);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopyError(true);
    }
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
      <p>
        <span dir="rtl" lang="ar" className={amiri.className}>
          {title}
        </span>{" "}
        — {volumeNumber !== null ? `Volume ${volumeNumber}, ` : ""}Page {pageNumber}
      </p>
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={handleCopy} className="inline-flex min-h-11 items-center px-2 font-medium text-accent hover:underline">
          {copied ? "Copied" : copyError ? "Copy unavailable" : "Copy full citation"}
        </button>
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-11 items-center px-2 font-medium text-accent hover:underline"
        >
          View original source
        </a>
      </div>
    </div>
  );
}
