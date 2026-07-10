"use client";

import { useState } from "react";
import { amiri } from "@/lib/fonts";
import { formatCitation } from "@/lib/citation";

export function Citation({
  title,
  volumeNumber,
  pageNumber,
  sourceUrl,
}: {
  title: string;
  volumeNumber: number | null;
  pageNumber: number;
  sourceUrl: string;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(formatCitation({ title, volumeNumber, pageNumber }));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
      <p>
        <span dir="rtl" lang="ar" className={amiri.className}>
          {title}
        </span>{" "}
        — {volumeNumber !== null ? `Volume ${volumeNumber}, ` : ""}Page {pageNumber}
      </p>
      <div className="flex gap-3">
        <button type="button" onClick={handleCopy} className="font-medium text-accent hover:underline">
          {copied ? "Copied!" : "Copy citation"}
        </button>
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-accent hover:underline"
        >
          View original source
        </a>
      </div>
    </div>
  );
}
