export interface CitationInput {
  title: string;
  volumeNumber: number | null;
  pageNumber: number;
  pageEnd?: number | null;
  printedNumber?: string | null;
  publicId?: string | null;
  canonicalUrl?: string | null;
  sourceUrl?: string | null;
  accessedOn?: string | null;
}

/** "{title} — Volume {v}, Page {p}" (volume segment omitted if unknown).
 * Kept as a standalone function (no JSX) so it's trivial to reuse for the
 * "Copy citation" clipboard text without re-deriving it from rendered DOM. */
export function formatCitation({
  title,
  volumeNumber,
  pageNumber,
  pageEnd,
  printedNumber,
  publicId,
  canonicalUrl,
  sourceUrl,
  accessedOn,
}: CitationInput): string {
  const pages = pageEnd && pageEnd !== pageNumber ? `pp. ${pageNumber}–${pageEnd}` : `p. ${pageNumber}`;
  const location = [volumeNumber !== null ? `vol. ${volumeNumber}` : null, pages, printedNumber ? `hadith ${printedNumber}` : null]
    .filter(Boolean)
    .join(", ");
  const record = publicId ? `Usul16 record ${publicId}` : "Usul16";
  const links = [canonicalUrl, sourceUrl && sourceUrl !== canonicalUrl ? `Source: ${sourceUrl}` : null].filter(Boolean);
  return [`${title}. ${location}.`, record, ...links, accessedOn ? `Accessed ${accessedOn}.` : null]
    .filter(Boolean)
    .join(" ");
}
