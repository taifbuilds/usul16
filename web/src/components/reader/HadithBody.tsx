"use client";

import Link from "next/link";
import { Fragment, useEffect, useMemo, useState, type ReactNode } from "react";
import type {
  ChainNodeRead,
  ChainRead,
  HadithChainsRead,
  HadithCommentarySummaryRead,
  HadithFootnote,
  HadithGrading,
  HadithTranslationRead,
  PersonRef,
} from "@/lib/api/types";
import { getHadithChains } from "@/lib/api/books";
import { formatArabicText } from "@/lib/arabic";
import { INLINE_RE, normaliseMarker } from "@/lib/inline";
import { isPublicHumanTranslation } from "@/lib/translationPublication";
import { ApparatusShelf } from "@/components/reader/ApparatusShelf";
import { GradingChips } from "@/components/reader/GradingChips";
import { DisclosureChevron } from "@/components/ui/DisclosureChevron";

// Interactive hadith text: footnote markers («[٤]») are tappable and expand
// the attached footnote inline, right under the paragraph being read —
// footnotes are part of the hadith, not a page-level appendix. A grouped
// «الهوامش» list at the card foot keeps everything reviewable at once, with
// per-page attribution because printed marker numbers restart on each page.

// Every narrator popover shares one `name`, which makes them a native exclusive
// accordion: opening one closes the rest. Without this, tapping narrator after
// narrator leaves a stack of open cards covering the text.
const NARRATOR_POPOVER_GROUP = "usul16-narrator-popover";

/** Close any open narrator popover on outside-click or Escape. `<details name>`
 * makes them mutually exclusive but never closes the last one. */
function useDismissNarratorPopovers(): void {
  useEffect(() => {
    const closeAll = (except: Element | null) => {
      document
        .querySelectorAll<HTMLDetailsElement>(`details[name="${NARRATOR_POPOVER_GROUP}"][open]`)
        .forEach((el) => {
          if (el !== except) el.open = false;
        });
    };
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Element | null;
      closeAll(target?.closest(`details[name="${NARRATOR_POPOVER_GROUP}"]`) ?? null);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeAll(null);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);
}

type Segment =
  | { type: "text"; content: string }
  | { type: "honorific"; content: string }
  | { type: "marker"; content: string; footnoteIndex: number | null };

interface NodeRange {
  start: number;
  end: number;
  node: ChainNodeRead;
}

function segment(text: string, claimFootnote: (marker: string) => number | null): Segment[] {
  const segments: Segment[] = [];
  let last = 0;
  for (const match of text.matchAll(INLINE_RE)) {
    const index = match.index ?? 0;
    if (index > last) segments.push({ type: "text", content: text.slice(last, index) });
    if (match[1]) {
      segments.push({
        type: "marker",
        content: match[1].replace(/\s/g, ""),
        footnoteIndex: claimFootnote(match[1]),
      });
    } else {
      segments.push({ type: "honorific", content: match[2] });
    }
    last = index + match[0].length;
  }
  if (last < text.length) segments.push({ type: "text", content: text.slice(last) });
  return segments;
}

function FootnoteInset({
  footnote,
  onClose,
}: {
  footnote: HadithFootnote;
  onClose: () => void;
}) {
  return (
    <div className="mt-3 mb-4 border-y border-dotted border-gold/65 bg-surface-2/70 px-4 py-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-[1.1rem] leading-[2] text-foreground/90">
          <sup className="me-1 select-none text-[0.7em] font-medium text-gold">
            [{footnote.marker}]
          </sup>
          {footnote.text}
        </p>
        <button
          type="button"
          onClick={onClose}
          aria-label="إغلاق الهامش"
          className="mt-1 shrink-0 rounded-md px-2 text-muted hover:text-foreground"
        >
          ✕
        </button>
      </div>
      {footnote.page ? (
        <p className="mt-1 text-xs text-muted">ص {footnote.page}</p>
      ) : null}
    </div>
  );
}

function statusLabel(node: ChainNodeRead): string {
  if (node.narrator) {
    return node.confidence !== null ? `resolved ${node.confidence}%` : "resolved";
  }
  if (node.candidates.length > 0) return "ambiguous";
  if (node.node_type === "collective_phrase") return "collective";
  if (node.node_type === "pronoun_relation") return node.relation_kind ?? "relation";
  return "unresolved";
}

function chipClass(node: ChainNodeRead): string {
  if (node.narrator) return "border-accent/40 bg-badge-verified text-accent";
  if (node.candidates.length > 0) return "border-gold/50 bg-badge text-foreground";
  if (node.node_type === "collective_phrase") return "border-dashed border-border bg-background text-muted";
  return "border-border bg-background text-muted";
}

function personHref(person: PersonRef | null): string | null {
  return person?.narrator_id ? `/narrators/${person.narrator_id}` : null;
}

function generationLabel(person: PersonRef | null): string | null {
  return person?.generation !== null && person?.generation !== undefined ? `g${person.generation}` : null;
}

function personResolutionLabel(node: ChainNodeRead): string {
  const resolution = node.person_resolution;
  if (!resolution) return statusLabel(node);
  const gen = generationLabel(resolution.resolved_person);
  if (resolution.status === "via_collective") return gen ? `via collective ${gen}` : "via collective";
  if (resolution.resolved_person) return gen ? `person ${gen}` : "person";
  if (resolution.status === "ambiguous" || resolution.candidates.length > 0) return "person ambiguous";
  if (resolution.status === "latent") return "latent person";
  return "person unresolved";
}

function personChipClass(node: ChainNodeRead): string {
  const resolution = node.person_resolution;
  if (!resolution) return chipClass(node);
  if (resolution.resolved_person) return "border-accent/40 bg-badge-verified text-accent";
  if (resolution.status === "ambiguous" || resolution.candidates.length > 0) {
    return "border-gold/50 bg-badge text-foreground";
  }
  if (resolution.status === "via_collective") return "border-accent/40 bg-badge-verified text-accent";
  return "border-border bg-background text-muted";
}

function PersonName({ person }: { person: PersonRef }) {
  const href = personHref(person);
  const content = (
    <>
      <span className="block">{formatArabicText(person.canonical_name_ar)}</span>
      <span className="mt-0.5 block text-xs text-muted">
        {person.kind}
        {generationLabel(person) ? ` - ${generationLabel(person)}` : ""}
      </span>
    </>
  );
  if (!href) return <div className="rounded-md border border-border px-2.5 py-2">{content}</div>;
  return (
    <Link href={href} className="block rounded-md border border-border px-2.5 py-2 hover:border-accent hover:text-accent">
      {content}
    </Link>
  );
}

function PersonResolutionPopover({ node }: { node: ChainNodeRead }) {
  const resolution = node.person_resolution;
  if (!resolution) return null;
  const candidates = resolution.candidates.slice(0, 6);

  return (
    <div className="absolute right-0 z-20 mt-2 w-80 rounded-lg border border-border bg-surface p-3 text-sm shadow-lg">
      <p className="mb-2 text-xs font-medium text-muted">Person identity</p>
      {resolution.resolved_person ? (
        <div className="mb-2">
          <PersonName person={resolution.resolved_person} />
        </div>
      ) : null}
      {resolution.primary_dalil ? (
        <p className="mb-2 rounded-md bg-background px-2.5 py-2 text-xs leading-relaxed text-muted">
          {formatArabicText(resolution.primary_dalil)}
        </p>
      ) : null}
      {candidates.length > 0 ? (
        <div className="space-y-2">
          {!resolution.resolved_person ? <p className="text-xs font-medium text-muted">Ranked candidates</p> : null}
          {candidates.map((candidate) => (
            <div key={`${node.id}-${candidate.rank}-${candidate.person?.id ?? "none"}`} className="space-y-1">
              {candidate.person ? <PersonName person={candidate.person} /> : null}
              <p className="text-xs text-muted">
                rank {candidate.rank} - {candidate.status}
                {candidate.method ? ` - ${candidate.method}` : ""}
              </p>
              {candidate.evidence_summary && candidate.evidence_summary !== resolution.primary_dalil ? (
                <p className="rounded-md bg-background px-2.5 py-2 text-xs leading-relaxed text-muted">
                  {formatArabicText(candidate.evidence_summary)}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function alignChar(value: string): string {
  if (/[\u064b-\u065f\u0670\u0640]/.test(value)) return "";
  if (/[\u200c\u200d]/.test(value)) return "";
  if (/[أإآٱ]/.test(value)) return "ا";
  if (value === "ى") return "ي";
  if (value === "ك") return "ك";
  if (value === "ک") return "ك";
  if (value === "ي" || value === "ی") return "ي";
  return value;
}

function alignmentIndex(text: string): { normalised: string; map: number[] } {
  const chars: string[] = [];
  const map: number[] = [];
  for (let i = 0; i < text.length; i += 1) {
    if (text[i] === "[") {
      const close = text.indexOf("]", i + 1);
      if (close !== -1) {
        i = close;
        continue;
      }
    }
    const next = alignChar(text[i]);
    if (!next) continue;
    chars.push(next);
    map.push(i);
  }
  return { normalised: chars.join(""), map };
}

function normaliseForAlignment(text: string): string {
  return alignmentIndex(formatArabicText(text)).normalised;
}

function originalCursorToNormalised(map: number[], cursor: number): number {
  const index = map.findIndex((position) => position >= cursor);
  return index === -1 ? map.length : index;
}

function extendPastDiacritics(text: string, end: number): number {
  let next = end;
  while (next < text.length && /[\u064b-\u065f\u0670\u200c\u200d]/.test(text[next])) {
    next += 1;
  }
  return next;
}

function buildNodeRanges(text: string, chain: ChainRead | null): NodeRange[] {
  if (!chain) return [];
  const source = alignmentIndex(text);
  const ranges: NodeRange[] = [];
  let cursor = 0;

  for (const node of chain.nodes) {
    const needle = normaliseForAlignment(node.raw_token);
    if (!needle.trim()) continue;
    const normalisedCursor = originalCursorToNormalised(source.map, cursor);
    const found = source.normalised.indexOf(needle, normalisedCursor);
    if (found === -1) continue;
    const start = source.map[found];
    const lastMapped = source.map[found + needle.length - 1];
    if (start === undefined || lastMapped === undefined || start < cursor) continue;
    const end = extendPastDiacritics(text, lastMapped + 1);
    ranges.push({ start, end, node });
    cursor = end;
  }

  return ranges;
}

function renderDecoratedText(text: string, keyPrefix: string): ReactNode[] {
  return segment(text, () => null).map((seg, index) => {
    if (seg.type === "text") return <Fragment key={`${keyPrefix}-${index}`}>{seg.content}</Fragment>;
    if (seg.type === "honorific") {
      return (
        <span key={`${keyPrefix}-${index}`} className="mx-1 text-[0.7em] text-accent">
          {seg.content}
        </span>
      );
    }
    return (
      <sup key={`${keyPrefix}-${index}`} className="mx-0.5 select-none text-[0.55em] font-medium text-gold">
        {seg.content}
      </sup>
    );
  });
}

function ChainNodeChip({ node }: { node: ChainNodeRead }) {
  const label = formatArabicText(node.raw_token);
  const phrase = node.transmission_phrase ? formatArabicText(node.transmission_phrase) : null;

  if (node.person_resolution) {
    // A pronoun_relation token is a verb+pronoun («سأله») or a relational word
    // («أبيه», «عنه»), not a name — showing the raw token reads like a narrator.
    // When it is resolved, label the chip with the person it refers to instead.
    const resolvedPerson = node.person_resolution.resolved_person;
    const displayLabel =
      node.node_type === "pronoun_relation" && resolvedPerson
        ? formatArabicText(resolvedPerson.canonical_name_ar)
        : label;
    return (
      <span className="inline-flex items-center gap-1.5">
        {phrase ? <span className="text-muted/70">{phrase}</span> : null}
        <details name={NARRATOR_POPOVER_GROUP} className="group relative inline-block">
          <summary
            className={`inline-flex min-h-6 cursor-pointer list-none items-center rounded-full border px-2.5 py-1 ${personChipClass(node)}`}
            title={node.person_resolution.primary_dalil ?? personResolutionLabel(node)}
          >
            <span>{displayLabel}</span>
            <span className="ms-1 text-[0.65em] opacity-70">{personResolutionLabel(node)}</span>
          </summary>
          <PersonResolutionPopover node={node} />
        </details>
      </span>
    );
  }

  if (node.narrator) {
    return (
      <span className="inline-flex items-center gap-1.5">
        {phrase ? <span className="text-muted/70">{phrase}</span> : null}
        <Link
          href={`/narrators/${node.narrator.id}`}
          title={node.resolution_reason ?? node.narrator.canonical_name_ar}
          className={`inline-flex min-h-6 items-center rounded-full border px-2.5 py-1 transition hover:border-accent hover:text-accent ${chipClass(node)}`}
        >
          <span>{label}</span>
          <span className="ms-1 text-[0.65em] opacity-70">{statusLabel(node)}</span>
        </Link>
      </span>
    );
  }

  if (node.candidates.length > 0) {
    return (
      <span className="inline-flex items-center gap-1.5">
        {phrase ? <span className="text-muted/70">{phrase}</span> : null}
        <details name={NARRATOR_POPOVER_GROUP} className="group relative inline-block">
          <summary
            className={`inline-flex min-h-6 cursor-pointer list-none items-center rounded-full border px-2.5 py-1 ${chipClass(node)}`}
            title={node.resolution_reason ?? "Multiple possible narrator identities"}
          >
            <span>{label}</span>
            <span className="ms-1 text-[0.65em] opacity-70">ambiguous</span>
          </summary>
          <div className="absolute right-0 z-20 mt-2 w-72 rounded-lg border border-border bg-surface p-3 text-sm shadow-lg">
            <p className="mb-2 text-xs font-medium text-muted">Possible identities</p>
            <div className="space-y-2">
              {node.candidates.map((candidate) => (
                <Link
                  key={`${node.id}-${candidate.narrator.id}`}
                  href={`/narrators/${candidate.narrator.id}`}
                  className="block rounded-md border border-border px-2.5 py-2 hover:border-accent hover:text-accent"
                >
                  <span className="block">{formatArabicText(candidate.narrator.canonical_name_ar)}</span>
                  <span className="mt-0.5 block text-xs text-muted">
                    rank {candidate.rank} · score {candidate.score} · {candidate.match_type}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </details>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5">
      {phrase ? <span className="text-muted/70">{phrase}</span> : null}
      <span
        className={`rounded-full border px-2.5 py-1 ${chipClass(node)}`}
        title={node.resolution_reason ?? statusLabel(node)}
      >
        <span>{label}</span>
        <span className="ms-1 text-[0.65em] opacity-70">{statusLabel(node)}</span>
      </span>
    </span>
  );
}

function InlineIsnadNode({
  node,
  text,
  nodeKey,
}: {
  node: ChainNodeRead;
  text: string;
  nodeKey: string;
}) {
  const className = `rounded px-1.5 py-0.5 transition ${personChipClass(node)}`;

  if (node.person_resolution) {
    const resolvedHref = personHref(node.person_resolution.resolved_person);
    if (resolvedHref) {
      return (
        <Link
          href={resolvedHref}
          title={node.person_resolution.primary_dalil ?? node.person_resolution.resolved_person?.canonical_name_ar}
          className={`${className} hover:border-accent hover:text-accent`}
        >
          {renderDecoratedText(text, nodeKey)}
        </Link>
      );
    }

    return (
      <details name={NARRATOR_POPOVER_GROUP} className="relative inline-block">
        <summary
          className={`inline cursor-pointer list-none ${className}`}
          title={node.person_resolution.primary_dalil ?? personResolutionLabel(node)}
        >
          {renderDecoratedText(text, nodeKey)}
        </summary>
        <PersonResolutionPopover node={node} />
      </details>
    );
  }

  if (node.narrator) {
    return (
      <Link
        href={`/narrators/${node.narrator.id}`}
        title={node.resolution_reason ?? node.narrator.canonical_name_ar}
        className={`${className} hover:border-accent hover:text-accent`}
      >
        {renderDecoratedText(text, nodeKey)}
      </Link>
    );
  }

  if (node.candidates.length > 0) {
    return (
      <details name={NARRATOR_POPOVER_GROUP} className="relative inline-block">
        <summary
          className={`inline cursor-pointer list-none ${className}`}
          title={node.resolution_reason ?? "Multiple possible narrator identities"}
        >
          {renderDecoratedText(text, nodeKey)}
        </summary>
        <div className="absolute right-0 z-20 mt-2 w-72 rounded-lg border border-border bg-surface p-3 text-sm shadow-lg">
          <p className="mb-2 text-xs font-medium text-muted">Possible identities</p>
          <div className="space-y-2">
            {node.candidates.map((candidate) => (
              <Link
                key={`${node.id}-${candidate.narrator.id}`}
                href={`/narrators/${candidate.narrator.id}`}
                className="block rounded-md border border-border px-2.5 py-2 hover:border-accent hover:text-accent"
              >
                <span className="block">{formatArabicText(candidate.narrator.canonical_name_ar)}</span>
                <span className="mt-0.5 block text-xs text-muted">
                  rank {candidate.rank} · score {candidate.score} · {candidate.match_type}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </details>
    );
  }

  return (
    <span className={className} title={node.resolution_reason ?? statusLabel(node)}>
      {renderDecoratedText(text, nodeKey)}
    </span>
  );
}

function ClickableIsnadText({ text, chain }: { text: string; chain: ChainRead | null }) {
  const ranges = buildNodeRanges(text, chain);
  if (!chain || ranges.length < Math.max(2, Math.floor(chain.nodes.length * 0.5))) {
    return <>{renderDecoratedText(text, "isnad-plain")}</>;
  }

  const nodes: ReactNode[] = [];
  let cursor = 0;
  ranges.forEach((range, index) => {
    if (range.start > cursor) {
      nodes.push(...renderDecoratedText(text.slice(cursor, range.start), `isnad-gap-${index}`));
    }
    nodes.push(
      <InlineIsnadNode
        key={`isnad-node-${range.node.id}`}
        node={range.node}
        text={text.slice(range.start, range.end)}
        nodeKey={`isnad-node-${range.node.id}`}
      />
    );
    cursor = range.end;
  });
  if (cursor < text.length) {
    nodes.push(...renderDecoratedText(text.slice(cursor), "isnad-tail"));
  }
  return <>{nodes}</>;
}

function ChainGraph({ chain }: { chain: ChainRead }) {
  const flags = chain.flags?.split(",").filter(Boolean) ?? [];
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
        <span>
          Chain {chain.chain_number} · {chain.nodes.length} nodes · {chain.review_status}
        </span>
        {flags.length > 0 ? <span>parser flags: {flags.join(", ")}</span> : null}
      </div>
      <div dir="rtl" lang="ar" className="flex flex-wrap items-center gap-2 text-right text-base leading-loose">
        {chain.nodes.map((node) => (
          <ChainNodeChip key={node.id} node={node} />
        ))}
      </div>
    </div>
  );
}

function IsnadGraphPanel({
  publicId,
  chains,
  loading,
  error,
  onLoad,
}: {
  publicId: string | null;
  chains: HadithChainsRead | null;
  loading: boolean;
  error: string | null;
  onLoad: () => void;
}) {
  if (!publicId) return null;

  return (
    <details
      className="group mb-4 border-b border-dashed border-border pb-4"
      onToggle={(event) => {
        if (event.currentTarget.open) onLoad();
      }}
    >
      <summary className="cursor-pointer list-none text-sm font-medium text-accent hover:underline">
        Show clickable narrator chain
      </summary>
      <div className="mt-3 rounded-lg border border-border bg-background/60 px-3 py-3">
        {loading ? <p className="text-sm text-muted">Loading narrator graph...</p> : null}
        {error ? <p className="text-sm text-muted">{error}</p> : null}
        {!loading && !error && chains?.chains.length === 0 ? (
          <p className="text-sm text-muted">No parsed chain is available for this hadith yet.</p>
        ) : null}
        {chains?.chains.length ? (
          <div className="space-y-4">
            {chains.chains.map((chain) => (
              <ChainGraph key={chain.id} chain={chain} />
            ))}
          </div>
        ) : null}
      </div>
    </details>
  );
}

export function HadithBody({
  publicId,
  isnad,
  matn,
  footnotes,
  translation,
  gradings,
  commentaries,
}: {
  publicId?: string | null;
  isnad: string | null;
  matn: string;
  footnotes: HadithFootnote[] | null;
  translation?: HadithTranslationRead | null;
  gradings?: HadithGrading[] | null;
  commentaries?: HadithCommentarySummaryRead[] | null;
}) {
  useDismissNarratorPopovers();
  const [active, setActive] = useState<string | null>(null);
  const [chainData, setChainData] = useState<HadithChainsRead | null>(null);
  const [chainLoading, setChainLoading] = useState(false);
  const [chainError, setChainError] = useState<string | null>(null);
  const notes = useMemo(() => footnotes ?? [], [footnotes]);
  const primaryChain = chainData?.chains[0] ?? null;
  // Several sharhs can comment on the same hadith; the API returns them in a
  // stable order, so render each rather than looking one source up by name.
  const sharhs = commentaries ?? [];

  function loadChains() {
    if (!publicId || chainData || chainLoading) return;
    setChainLoading(true);
    setChainError(null);
    getHadithChains(publicId)
      .then((data) => setChainData(data))
      .catch((err: unknown) => {
        setChainError(err instanceof Error ? err.message : "Could not load chain graph");
      })
      .finally(() => setChainLoading(false));
  }

  // Markers repeat across the pages a hadith spans, so the nth occurrence of
  // a marker in reading order claims the nth footnote carrying that marker.
  const paragraphs = useMemo(() => {
    const used = new Array(notes.length).fill(false);
    const claim = (marker: string): number | null => {
      const wanted = normaliseMarker(marker);
      for (let i = 0; i < notes.length; i += 1) {
        if (!used[i] && normaliseMarker(notes[i].marker) === wanted) {
          used[i] = true;
          return i;
        }
      }
      return null;
    };
    const built: { key: string; kind: "isnad" | "matn"; segments: Segment[] }[] = [];
    if (isnad) built.push({ key: "isnad", kind: "isnad", segments: segment(isnad, claim) });
    built.push({ key: "matn", kind: "matn", segments: segment(matn, claim) });
    return built;
  }, [isnad, matn, notes]);
  const publicTranslation = isPublicHumanTranslation(translation) ? translation : null;

  const renderSegments = (paragraphKey: string, segments: Segment[]): ReactNode[] =>
    segments.map((seg, index) => {
      if (seg.type === "text") return <Fragment key={index}>{seg.content}</Fragment>;
      if (seg.type === "honorific") {
        return (
          <span key={index} className="mx-1 text-[0.7em] text-accent">
            {seg.content}
          </span>
        );
      }
      if (seg.footnoteIndex === null) {
        return (
          <sup key={index} className="mx-0.5 select-none text-[0.55em] font-medium text-gold">
            {seg.content}
          </sup>
        );
      }
      const id = `${paragraphKey}:${seg.footnoteIndex}`;
      const isOpen = active === id;
      return (
        <button
          key={index}
          type="button"
          onClick={() => setActive(isOpen ? null : id)}
          aria-expanded={isOpen}
          title="اعرض الهامش"
          className={`mx-0.5 -my-1 inline-flex min-h-6 min-w-6 items-center justify-center rounded px-0.5 align-super text-[0.55em] font-semibold transition ${
            isOpen ? "bg-gold/20 text-gold" : "text-gold hover:bg-gold/10"
          }`}
        >
          {seg.content}
        </button>
      );
    });

  return (
    <div className="min-w-0 max-w-full overflow-hidden">
      {paragraphs.map((paragraph) => {
        const activeIndex =
          active && active.startsWith(`${paragraph.key}:`)
            ? Number(active.slice(paragraph.key.length + 1))
            : null;
        return (
          <div key={paragraph.key}>
            {paragraph.kind === "isnad" ? (
              <>
                {/* A div, not a p: every clickable narrator is a
                    <details>/<summary> popover, and <summary> may not
                    descend from <p>. The browser closed the paragraph early
                    and React threw a hydration error on every reader page
                    carrying a parsed chain. Styling is by class, not tag. */}
                <div className="reader-isnad mb-4 border-b border-dashed border-border pb-4 text-lg leading-loose text-muted">
                  {primaryChain && isnad ? (
                    <ClickableIsnadText text={isnad} chain={primaryChain} />
                  ) : (
                    renderSegments(paragraph.key, paragraph.segments)
                  )}
                </div>
                <IsnadGraphPanel
                  publicId={publicId ?? null}
                  chains={chainData}
                  loading={chainLoading}
                  error={chainError}
                  onLoad={loadChains}
                />
              </>
            ) : (
              <p className="reader-matn text-justify text-2xl leading-[2.2]">
                {renderSegments(paragraph.key, paragraph.segments)}
              </p>
            )}
            {activeIndex !== null && notes[activeIndex] ? (
              <FootnoteInset footnote={notes[activeIndex]} onClose={() => setActive(null)} />
            ) : null}
          </div>
        );
      })}

      {publicId ? (
        <ApparatusShelf
          publicId={publicId}
          commentaries={sharhs}
          translation={publicTranslation}
        />
      ) : null}

      {gradings && gradings.length > 0 ? (
        <div dir="ltr" lang="en" className="mt-5 text-left">
          <GradingChips gradings={gradings} />
        </div>
      ) : null}

      {notes.length > 0 ? (
        <details className="group mt-7">
          <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between border-t-2 border-dotted border-gold/75 px-1 py-2 transition-colors hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent/35">
            <span className="flex items-baseline gap-2">
              <span className="text-base font-semibold text-foreground">الهوامش</span>
              <span className="text-sm text-gold">{notes.length}</span>
            </span>
            <DisclosureChevron className="me-2 text-muted transition group-open:rotate-180" />
          </summary>
          <div className="space-y-4 border-t border-dotted border-gold/45 px-1 py-4">
            {notes.map((footnote, index) => (
              <p key={index} className="text-[1.1rem] leading-[2] text-muted">
                <sup className="me-1 select-none text-[0.7em] font-medium text-gold">
                  [{footnote.marker}]
                </sup>
                {footnote.text}
                {footnote.page ? (
                  <span className="ms-2 text-xs text-muted/70">ص {footnote.page}</span>
                ) : null}
              </p>
            ))}
          </div>
        </details>
      ) : null}
    </div>
  );
}
