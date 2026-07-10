export interface CitationInput {
  title: string;
  volumeNumber: number | null;
  pageNumber: number;
}

/** "{title} — Volume {v}, Page {p}" (volume segment omitted if unknown).
 * Kept as a standalone function (no JSX) so it's trivial to reuse for the
 * "Copy citation" clipboard text without re-deriving it from rendered DOM. */
export function formatCitation({ title, volumeNumber, pageNumber }: CitationInput): string {
  const location = volumeNumber !== null ? `Volume ${volumeNumber}, Page ${pageNumber}` : `Page ${pageNumber}`;
  return `${title} — ${location}`;
}
