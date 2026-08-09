import type { ReactNode } from "react";
import Link from "next/link";
import type { HadithRead, PageRead } from "@/lib/api/types";
import { formatArabicText } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";
import { INLINE_RE } from "@/lib/inline";
import { parsePageBlocks, parsePageText, type Footnote, type HadithUnit } from "@/lib/hadith";
import { HadithBody } from "@/components/reader/HadithBody";
import { TopicChips } from "@/components/topics/TopicChips";
import { EmptyState } from "@/components/ui/EmptyState";
import { DisclosureChevron } from "@/components/ui/DisclosureChevron";

// Bold the classical commentary openers (بيان، أقول…) at the start of a
// plain-text unit so the apparatus reads distinctly from narration.
const OPENER_RE = /^(بيان|أقول|توضيح|إيضاح|تبيين|تبيان|شرح|فالوجه|قال الشيخ|قال مصنف هذا الكتاب|ورواه)/;

function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let last = 0;
  let key = 0;
  for (const match of text.matchAll(INLINE_RE)) {
    const index = match.index ?? 0;
    if (index > last) nodes.push(text.slice(last, index));
    if (match[1]) {
      nodes.push(
        <sup key={key++} className="mx-0.5 select-none text-[0.55em] font-medium text-gold">
          {match[1].replace(/\s/g, "")}
        </sup>
      );
    } else {
      nodes.push(
        <span key={key++} className="mx-1 text-[0.7em] text-accent">
          {match[2]}
        </span>
      );
    }
    last = index + match[0].length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

function HadithCard({ unit }: { unit: HadithUnit }) {
  return (
    <article className="reader-record border border-border bg-surface p-4 sm:p-7">
      <div className="mb-4 flex items-center justify-between gap-3">
        {unit.kind === "continuation" ? (
          <span className="rounded-full border border-dashed border-border px-3 py-1 text-xs text-muted">
            تتمّة من الصفحة السابقة
          </span>
        ) : (
          <span className="text-xs tracking-wide text-muted/70 uppercase">Hadith</span>
        )}
        {unit.number ? (
          <span className="rounded-full bg-badge px-3 py-1 text-sm font-medium text-badge-foreground">
            {unit.number}
          </span>
        ) : null}
      </div>

      {unit.isnad ? (
        <p className="reader-isnad mb-4 border-b border-dashed border-border pb-4 text-lg leading-loose text-muted">
          {renderInline(formatArabicText(unit.isnad))}
        </p>
      ) : null}

      <p className="reader-matn text-justify text-2xl leading-[2.2]">
        {renderInline(formatArabicText(unit.matn ?? unit.text ?? ""))}
      </p>

      {unit.notes?.length ? (
        <div className="mt-5 space-y-3 border-t border-dashed border-border pt-4">
          {unit.notes.map((note, index) => (
            <NoteParagraph key={index} text={note} />
          ))}
        </div>
      ) : null}
    </article>
  );
}

function pageRangeLabel(hadith: HadithRead): string {
  if (hadith.volume_start !== hadith.volume_end && hadith.volume_end !== null) {
    return `v${hadith.volume_start ?? "?"} p${hadith.page_start} -> v${hadith.volume_end} p${hadith.page_end}`;
  }
  if (hadith.page_end !== hadith.page_start) {
    return `pages ${hadith.page_start}-${hadith.page_end}`;
  }
  return `page ${hadith.page_start}`;
}

type PagePosition = "single" | "start" | "middle" | "end";

function pagePosition(
  hadith: HadithRead,
  currentVolume: number | null,
  currentPage: number | undefined
): PagePosition {
  if (currentPage === undefined) return "single";

  const startsHere = hadith.volume_start === currentVolume && hadith.page_start === currentPage;
  const endsHere = hadith.volume_end === currentVolume && hadith.page_end === currentPage;

  if (startsHere && endsHere) return "single";
  if (startsHere) return "start";
  if (endsHere) return "end";
  return "middle";
}

function pagePositionNote(hadith: HadithRead, position: PagePosition): string | null {
  const range = pageRangeLabel(hadith);
  if (position === "start") {
    return `Complete indexed hadith starts here; printed across ${range}.`;
  }
  if (position === "middle") {
    return `Same indexed hadith ${hadith.public_id}; it began on ${range}.`;
  }
  if (position === "end") {
    return `Same indexed hadith ${hadith.public_id}; it ends on this printed page after beginning on ${range}.`;
  }

  return null;
}

export function IndexedHadithCard({
  hadith,
  currentVolume,
  currentPage,
}: {
  hadith: HadithRead;
  currentVolume?: number | null;
  currentPage?: number;
}) {
  const position = pagePosition(hadith, currentVolume ?? null, currentPage);
  const note = pagePositionNote(hadith, position);
  const isCarryover = currentPage !== undefined && (position === "middle" || position === "end");
  const citationHref = `/read/${hadith.book_id}/${hadith.volume_start ?? 1}/${hadith.page_start}`;
  const chapterNumber = hadith.structure?.number_in_chapter ?? null;
  const body = (
    <HadithBody
      publicId={hadith.public_id}
      isnad={hadith.isnad_raw ? formatArabicText(hadith.isnad_raw) : null}
      matn={formatArabicText(hadith.matn_raw)}
      footnotes={hadith.footnotes}
      translation={hadith.translation}
      gradings={hadith.gradings}
      commentaries={hadith.commentaries}
    />
  );

  return (
    <article
      id={`hadith-${hadith.id}`}
      className="reader-record min-w-0 max-w-full overflow-hidden scroll-mt-24 border border-border bg-surface p-4 sm:p-7"
    >
      <header dir="ltr" className="mb-5 flex flex-wrap items-center justify-between gap-x-5 gap-y-2 border-b border-border pb-3 font-sans text-xs text-muted">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          {hadith.printed_number ? (
            <span className="font-mono font-semibold text-foreground">
              No. {hadith.printed_number}
            </span>
          ) : null}
          {chapterNumber !== null ? (
            <span
              title="Hadith number within its chapter"
              className="font-mono font-medium text-gold"
            >
              chapter #{chapterNumber}
            </span>
          ) : null}
          <Link
            href={citationHref}
            title="Open in printed-page view"
            className="transition-colors hover:text-accent hover:underline"
          >
            {hadith.volume_start !== null ? `vol. ${hadith.volume_start} · ` : ""}
            {pageRangeLabel(hadith)}
          </Link>
        </div>
        <Link
          href={`/hadith/${encodeURIComponent(hadith.public_id)}`}
          title="Permanent link - this hadith's unique ID"
          className="font-mono transition-colors hover:text-accent hover:underline"
        >
          {hadith.public_id}
        </Link>
      </header>

      {note ? (
        <p className="mb-4 border-b border-dashed border-border pb-3 text-xs text-muted">
          {note}
        </p>
      ) : null}

      {isCarryover ? (
        <details className="group">
          <summary className="inline-flex min-h-11 cursor-pointer list-none items-center text-sm font-medium text-accent hover:underline">
            Show complete hadith text
          </summary>
          <div className="mt-4">{body}</div>
        </details>
      ) : (
        body
      )}

      {hadith.topics.length ? (
        <footer dir="ltr" className="mt-6 border-t border-border pt-4 font-sans">
          <div className="mb-3 flex items-center justify-between gap-4 text-xs">
            <span className="font-semibold text-foreground">Topics</span>
            <span className="tabular-nums text-muted">{hadith.topics.length}</span>
          </div>
          <TopicChips topics={hadith.topics} compact />
        </footer>
      ) : null}
    </article>
  );
}

function TextParagraph({ text }: { text: string }) {
  const formatted = formatArabicText(text);
  const opener = OPENER_RE.exec(formatted);

  return (
    <p className="reader-prose px-1 text-justify text-xl leading-[2.1] text-foreground/90">
      {opener ? (
        <>
          <span className="font-bold text-accent">{opener[1]}</span>
          {renderInline(formatted.slice(opener[1].length))}
        </>
      ) : (
        renderInline(formatted)
      )}
    </p>
  );
}

function NoteParagraph({ text }: { text: string }) {
  const formatted = formatArabicText(text);
  const opener = OPENER_RE.exec(formatted);

  return (
    <p className="reader-note text-justify text-lg leading-[2] text-foreground/80">
      {opener ? (
        <>
          <span className="font-bold text-accent">{opener[1]}</span>
          {renderInline(formatted.slice(opener[1].length))}
        </>
      ) : (
        renderInline(formatted)
      )}
    </p>
  );
}

export function SectionHeading({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-4 pt-4 pb-2" role="heading" aria-level={2}>
      <span className="h-px flex-1 bg-border" />
      <h2 className="text-center text-2xl font-semibold leading-relaxed text-accent">
        {renderInline(formatArabicText(text))}
      </h2>
      <span className="h-px flex-1 bg-border" />
    </div>
  );
}

function FootnoteSection({ footnotes }: { footnotes: Footnote[] }) {
  return (
    <details className="group">
      <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between border-t-2 border-dotted border-gold/75 px-1 py-3 transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent/35">
        <span className="flex items-baseline gap-2">
          <span className="text-base font-semibold text-foreground">الهوامش</span>
          <span className="text-sm text-gold">
            {footnotes.length} footnote{footnotes.length === 1 ? "" : "s"}
          </span>
        </span>
        <DisclosureChevron className="me-2 text-muted transition group-open:rotate-180" />
      </summary>
      <div className="space-y-4 border-t border-dotted border-gold/45 px-1 py-4">
        {footnotes.map((footnote, index) => (
          <p key={index} className="text-[1.1rem] leading-[2] text-muted">
            <sup className="me-1 text-[0.7em] text-gold">[{footnote.marker}]</sup>
            {renderInline(formatArabicText(footnote.text))}
          </p>
        ))}
      </div>
    </details>
  );
}

export function ReaderText({ page, hadiths }: { page: PageRead; hadiths?: HadithRead[] }) {
  const parsed = page.text_blocks?.length
    ? parsePageBlocks(page.text_blocks, { bookId: page.book_id })
    : page.text_raw
      ? parsePageText(page.text_raw, { bookId: page.book_id })
      : { units: [], footnotes: [] };

  if (hadiths !== undefined) {
    if (hadiths.length === 0) {
      return (
        <div className="space-y-5">
          <EmptyState
            title="No indexed hadith on this page"
            description="This page is likely a heading, footnote area, or edition apparatus."
          />
          {parsed.footnotes.length > 0 ? <FootnoteSection footnotes={parsed.footnotes} /> : null}
        </div>
      );
    }

    return (
      <div dir="rtl" lang="ar" className={`${amiri.className} space-y-5 text-right`}>
        {hadiths.map((hadith, index) => {
          const showSection =
            hadith.section_title && (index === 0 || hadith.section_title !== hadiths[index - 1]?.section_title);
          return (
            <div key={hadith.id} className="space-y-5">
              {showSection ? <SectionHeading text={hadith.section_title ?? ""} /> : null}
              <IndexedHadithCard
                hadith={hadith}
                currentVolume={page.volume_number}
                currentPage={page.page_number}
              />
            </div>
          );
        })}
        {parsed.footnotes.length > 0 ? <FootnoteSection footnotes={parsed.footnotes} /> : null}
      </div>
    );
  }

  if (!parsed.units.length && !parsed.footnotes.length) {
    return (
      <EmptyState
        title="No text on this page"
        description="This is likely a scanned, image-only page; no selectable text was found when it was crawled."
      />
    );
  }

  return (
    <div dir="rtl" lang="ar" className={`${amiri.className} space-y-5 text-right`}>
      {parsed.units.map((unit, index) => {
        if (unit.kind === "heading") {
          return <SectionHeading key={index} text={unit.text ?? ""} />;
        }
        if (unit.kind === "text") {
          return <TextParagraph key={index} text={unit.text ?? ""} />;
        }
        return <HadithCard key={index} unit={unit} />;
      })}

      {parsed.footnotes.length > 0 ? <FootnoteSection footnotes={parsed.footnotes} /> : null}
    </div>
  );
}
