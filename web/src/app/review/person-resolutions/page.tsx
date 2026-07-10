import Link from "next/link";
import {
  getPersonResolutionAuditQueue,
  getPersonResolutionAuditSummary,
  getPersonResolutionDecisionSummary,
} from "@/lib/api/books";
import type {
  PersonResolutionAuditCandidate,
  PersonResolutionAuditItem,
  PersonResolutionAuditSummary,
  PersonResolutionDecisionSummary,
  PersonResolutionNodeTypeCount,
} from "@/lib/api/types";
import { formatArabicText } from "@/lib/arabic";

export const dynamic = "force-dynamic";

const DEFAULT_SOURCE_BOOK_ID = "11005";
const ADMIN_REVIEWER = "codex-admin-external-v1";
const STATUS_OPTIONS = [
  "open",
  "ambiguous",
  "unresolved",
  "latent",
  "missing_rank1",
  "resolved",
  "via_collective",
  "all",
];
const NODE_TYPE_OPTIONS = [
  "",
  "named_narrator",
  "imam",
  "collective_phrase",
  "pronoun_relation",
  "unknown_person",
];
const RISK_OPTIONS = [
  "",
  "any",
  "phase_d_context",
  "weak_surface",
  "shared_surface",
  "low_margin",
  "many_candidates",
];

function compactNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function statusLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function countFor(summary: PersonResolutionAuditSummary, status: string): number {
  return summary.status_counts.find((row) => row.status === status)?.total ?? 0;
}

function decisionCountFor(summary: PersonResolutionDecisionSummary, key: string): number {
  return summary.decision_counts.find((row) => row.key === key)?.total ?? 0;
}

function hrefWith(params: Record<string, string | number | null | undefined>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      query.set(key, String(value));
    }
  }
  return `/review/person-resolutions?${query.toString()}`;
}

function badgeClass(status: string): string {
  if (status === "resolved" || status === "via_collective") {
    return "border-accent/30 bg-badge-verified text-accent";
  }
  if (status === "ambiguous") return "border-gold/40 bg-badge text-badge-foreground";
  if (status === "unresolved" || status === "missing_rank1") {
    return "border-red-200 bg-red-50 text-red-800";
  }
  return "border-border bg-surface text-muted";
}

function nodeTypeRows(summary: PersonResolutionAuditSummary): PersonResolutionNodeTypeCount[] {
  return [...summary.node_type_counts].sort((a, b) =>
    a.node_type === b.node_type ? a.status.localeCompare(b.status) : a.node_type.localeCompare(b.node_type)
  );
}

function CandidateLine({ candidate }: { candidate: PersonResolutionAuditCandidate }) {
  const person = candidate.person;
  return (
    <li className="border-t border-border/70 py-2 first:border-t-0">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs text-muted">#{candidate.rank}</span>
        <span className={`rounded-full border px-2 py-0.5 text-xs ${badgeClass(candidate.status)}`}>
          {statusLabel(candidate.status)}
        </span>
        {candidate.method ? <span className="text-xs text-muted">{candidate.method}</span> : null}
        {candidate.score !== null ? (
          <span className="text-xs text-muted">score {candidate.score}</span>
        ) : null}
        {candidate.margin_to_winner !== null ? (
          <span className="text-xs text-muted">-{candidate.margin_to_winner}</span>
        ) : null}
      </div>
      {person ? (
        <div className="mt-1 text-sm font-medium" dir="rtl">
          {person.narrator_id ? (
            <Link href={`/narrators/${person.narrator_id}`} className="text-accent hover:underline">
              {formatArabicText(person.canonical_name_ar)}
            </Link>
          ) : (
            formatArabicText(person.canonical_name_ar)
          )}
          {person.generation !== null ? (
            <span className="ms-2 text-xs text-muted" dir="ltr">
              gen {person.generation}
            </span>
          ) : null}
        </div>
      ) : null}
      {candidate.evidence_summary ? (
        <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted">{candidate.evidence_summary}</p>
      ) : null}
    </li>
  );
}

function AuditItem({ item }: { item: PersonResolutionAuditItem }) {
  const page =
    item.page_start === item.page_end
      ? `p. ${item.page_start}`
      : `pp. ${item.page_start}-${item.page_end}`;
  const effectivePerson = item.effective_resolution?.person;
  return (
    <article className="rounded-lg border border-border bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/hadith/${encodeURIComponent(item.public_id)}`}
              className="font-mono text-sm font-semibold text-accent hover:underline"
            >
              {item.public_id}
            </Link>
            <span className="text-xs text-muted">
              chain {item.chain_number} / pos {item.position}
            </span>
            <span className="text-xs text-muted">
              vol. {item.volume_start ?? "?"} {page}
            </span>
          </div>
          {item.section_title ? <p className="mt-1 text-xs text-muted">{item.section_title}</p> : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <span className={`rounded-full border px-2 py-1 text-xs ${badgeClass(item.status)}`}>
            {statusLabel(item.status)}
          </span>
          <span className="rounded-full border border-border bg-background px-2 py-1 text-xs text-muted">
            {item.node_type}
          </span>
          {item.method ? (
            <span className="rounded-full border border-border bg-background px-2 py-1 text-xs text-muted">
              {item.method}
            </span>
          ) : null}
          {item.admin_decision ? (
            <span className="rounded-full border border-accent/30 bg-badge-verified px-2 py-1 text-xs text-accent">
              {statusLabel(item.admin_decision.decision_type)}
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-3 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(280px,360px)]">
        <div>
          <p className="text-xs font-medium text-muted">Token</p>
          <p className="mt-1 rounded-md border border-border bg-background px-3 py-2 font-arabic text-xl leading-9" dir="rtl">
            {formatArabicText(item.raw_token)}
          </p>

          {item.effective_resolution ? (
            <div className="mt-3 border-l-2 border-accent pl-3">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-xs font-medium text-muted">Effective result</p>
                <span className="rounded-full border border-accent/30 bg-badge-verified px-2 py-0.5 text-xs text-accent">
                  {item.effective_resolution.label}
                </span>
                <span className="text-xs text-muted">{item.effective_resolution.source}</span>
              </div>
              {effectivePerson ? (
                <p className="mt-1 text-sm font-medium" dir="rtl">
                  {effectivePerson.narrator_id ? (
                    <Link href={`/narrators/${effectivePerson.narrator_id}`} className="text-accent hover:underline">
                      {formatArabicText(effectivePerson.canonical_name_ar)}
                    </Link>
                  ) : (
                    formatArabicText(effectivePerson.canonical_name_ar)
                  )}
                </p>
              ) : (
                <p className="mt-1 text-sm text-muted">{statusLabel(item.effective_resolution.status)}</p>
              )}
              {item.admin_decision?.external_case_id ? (
                <p className="mt-1 font-mono text-xs text-muted">{item.admin_decision.external_case_id}</p>
              ) : null}
              {item.admin_decision?.source_reference ? (
                <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted">
                  {item.admin_decision.source_reference}
                </p>
              ) : null}
            </div>
          ) : null}

          {item.risk_flags.length ? (
            <div className="mt-2 flex flex-wrap gap-2">
              {item.risk_flags.map((flag) => (
                <span key={flag} className="rounded-full bg-badge px-2 py-1 text-xs text-badge-foreground">
                  {statusLabel(flag)}
                </span>
              ))}
            </div>
          ) : null}

          {item.primary_dalil ? (
            <p className="mt-3 text-sm leading-6 text-muted">{item.primary_dalil}</p>
          ) : null}

          {item.isnad_excerpt ? (
            <p className="mt-3 text-sm leading-7" dir="rtl">
              {formatArabicText(item.isnad_excerpt)}
            </p>
          ) : null}
          <p className="mt-2 line-clamp-2 text-xs leading-5 text-muted" dir="rtl">
            {formatArabicText(item.matn_excerpt)}
          </p>

          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <Link
              href={`/read/1178/${item.volume_start ?? 1}/${item.page_start}#hadith-${item.hadith_id}`}
              className="rounded-md border border-border px-2 py-1 text-accent hover:border-accent"
            >
              Reader
            </Link>
            <Link
              href={`/hadith/${encodeURIComponent(item.public_id)}`}
              className="rounded-md border border-border px-2 py-1 text-accent hover:border-accent"
            >
              Hadith
            </Link>
          </div>
        </div>

        <div className="rounded-md border border-border bg-background p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <p className="text-xs font-medium text-muted">Candidates</p>
            <p className="font-mono text-xs text-muted">{item.candidate_count}</p>
          </div>
          {item.candidates.length ? (
            <ol>
              {item.candidates.slice(0, 6).map((candidate) => (
                <CandidateLine
                  key={`${item.node_id}-${candidate.rank}-${candidate.person?.id ?? "none"}`}
                  candidate={candidate}
                />
              ))}
            </ol>
          ) : (
            <p className="text-sm text-muted">No person candidates.</p>
          )}
        </div>
      </div>
    </article>
  );
}

export default async function PersonResolutionAuditPage({
  searchParams,
}: {
  searchParams?: Promise<{
    source_book_id?: string;
    status?: string;
    node_type?: string;
    risk?: string;
    q?: string;
    admin_reviewed?: string;
    skip?: string;
    limit?: string;
  }>;
}) {
  const params = searchParams ? await searchParams : {};
  const sourceBookId = params.source_book_id ?? DEFAULT_SOURCE_BOOK_ID;
  const status = params.status ?? "open";
  const nodeType = params.node_type ?? "";
  const risk = params.risk ?? "";
  const q = params.q ?? "";
  const adminReviewed = params.admin_reviewed === "true" || params.admin_reviewed === "1";
  const skip = Math.max(0, Number(params.skip ?? 0) || 0);
  const limit = Math.min(200, Math.max(1, Number(params.limit ?? 50) || 50));

  const [summary, machineSummary, adminSummary, page] = await Promise.all([
    getPersonResolutionAuditSummary({ sourceBookId }),
    getPersonResolutionDecisionSummary({ sourceBookId }),
    getPersonResolutionDecisionSummary({ sourceBookId, reviewer: ADMIN_REVIEWER }),
    getPersonResolutionAuditQueue({
      sourceBookId,
      status,
      nodeType: nodeType || null,
      risk: risk || null,
      q: q || null,
      adminReviewed,
      skip,
      limit,
    }),
  ]);
  const resolved = countFor(summary, "resolved");
  const viaCollective = countFor(summary, "via_collective");
  const openPercent = summary.total_nodes
    ? Math.round((summary.open_nodes / summary.total_nodes) * 1000) / 10
    : 0;

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-medium tracking-wide text-muted uppercase">Tamyiz admin</p>
          <h1 className="mt-1 font-serif text-3xl font-semibold text-accent">
            Person-resolution audit
          </h1>
        </div>
        <form className="flex flex-wrap items-end gap-3">
          <label className="block text-sm">
            <span className="font-medium text-muted">Source book ID</span>
            <input
              name="source_book_id"
              defaultValue={sourceBookId}
              className="mt-1 w-32 rounded-lg border border-border bg-surface px-3 py-2 outline-none focus:border-accent"
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium text-muted">Status</span>
            <select
              name="status"
              defaultValue={status}
              className="mt-1 w-40 rounded-lg border border-border bg-surface px-3 py-2 outline-none focus:border-accent"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {statusLabel(option)}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="font-medium text-muted">Node type</span>
            <select
              name="node_type"
              defaultValue={nodeType}
              className="mt-1 w-44 rounded-lg border border-border bg-surface px-3 py-2 outline-none focus:border-accent"
            >
              {NODE_TYPE_OPTIONS.map((option) => (
                <option key={option || "all"} value={option}>
                  {option || "all"}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="font-medium text-muted">Risk</span>
            <select
              name="risk"
              defaultValue={risk}
              className="mt-1 w-44 rounded-lg border border-border bg-surface px-3 py-2 outline-none focus:border-accent"
            >
              {RISK_OPTIONS.map((option) => (
                <option key={option || "none"} value={option}>
                  {option ? statusLabel(option) : "none"}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="font-medium text-muted">Token</span>
            <input
              name="q"
              defaultValue={q}
              className="mt-1 w-48 rounded-lg border border-border bg-surface px-3 py-2 outline-none focus:border-accent"
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium text-muted">Limit</span>
            <input
              name="limit"
              type="number"
              min="1"
              max="200"
              defaultValue={limit}
              className="mt-1 w-24 rounded-lg border border-border bg-surface px-3 py-2 outline-none focus:border-accent"
            />
          </label>
          <label className="flex items-center gap-2 pb-2 text-sm text-muted">
            <input
              name="admin_reviewed"
              type="checkbox"
              value="true"
              defaultChecked={adminReviewed}
              className="h-4 w-4 accent-[var(--color-accent)]"
            />
            Admin reviewed
          </label>
          <button
            type="submit"
            className="rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-accent hover:border-accent"
          >
            Load
          </button>
        </form>
      </div>

      <section className="grid gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Total chain nodes</p>
          <p className="mt-1 font-mono text-2xl text-accent">{compactNumber(summary.total_nodes)}</p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Resolved</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(resolved + viaCollective)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Open</p>
          <p className="mt-1 font-mono text-2xl text-accent">{compactNumber(summary.open_nodes)}</p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Open share</p>
          <p className="mt-1 font-mono text-2xl text-accent">{openPercent}%</p>
        </div>
      </section>

      <section className="mt-3 grid gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Machine decisions</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(machineSummary.total_decisions)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Machine approved</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(decisionCountFor(machineSummary, "approve_current"))}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">External review</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(decisionCountFor(machineSummary, "needs_external_review"))}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Contradiction flags</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(decisionCountFor(machineSummary, "flag_contradiction"))}
          </p>
        </div>
      </section>

      <section className="mt-3 grid gap-3 md:grid-cols-5">
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">External admin</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(adminSummary.total_decisions)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Approved current</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(decisionCountFor(adminSummary, "approve_current"))}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Approved override</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(decisionCountFor(adminSummary, "approve_external_override"))}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Kept ambiguous</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(decisionCountFor(adminSummary, "keep_ambiguous"))}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-xs text-muted">Text or chain issue</p>
          <p className="mt-1 font-mono text-2xl text-accent">
            {compactNumber(decisionCountFor(adminSummary, "flag_text_or_chain_issue"))}
          </p>
        </div>
      </section>

      <div className="mt-3 flex flex-wrap gap-2">
        <Link
          href={hrefWith({
            source_book_id: sourceBookId,
            status: "all",
            admin_reviewed: "true",
            limit,
          })}
          className={`rounded-full border px-3 py-1 text-sm ${
            adminReviewed ? "border-accent bg-badge-verified text-accent" : "border-border text-muted"
          }`}
        >
          reviewed nodes {compactNumber(adminSummary.total_decisions)}
        </Link>
      </div>

      <section className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Link
              href={hrefWith({
                source_book_id: sourceBookId,
                status: "resolved",
                risk: "any",
                node_type: nodeType,
                q,
                limit,
              })}
              className={`rounded-full border px-3 py-1 text-sm ${
                status === "resolved" && risk === "any"
                  ? "border-accent bg-badge-verified text-accent"
                  : "border-border text-muted"
              }`}
            >
              risky resolved
            </Link>
            {RISK_OPTIONS.filter(Boolean).map((option) => (
              <Link
                key={option}
                href={hrefWith({
                  source_book_id: sourceBookId,
                  status: "resolved",
                  risk: option,
                  node_type: nodeType,
                  q,
                  limit,
                })}
                className={`rounded-full border px-3 py-1 text-sm ${
                  status === "resolved" && risk === option
                    ? "border-accent text-accent"
                    : "border-border text-muted"
                }`}
              >
                {statusLabel(option)}
              </Link>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {summary.status_counts.map((row) => (
              <Link
                key={row.status}
                href={hrefWith({
                  source_book_id: sourceBookId,
                  status: row.status,
                  node_type: nodeType,
                  risk,
                  q,
                  limit,
                })}
                className={`rounded-full border px-3 py-1 text-sm ${
                  row.status === status ? "border-accent text-accent" : "border-border text-muted"
                }`}
              >
                {statusLabel(row.status)} {compactNumber(row.total)}
              </Link>
            ))}
            <Link
              href={hrefWith({
                source_book_id: sourceBookId,
                status: "open",
                node_type: nodeType,
                q,
                limit,
              })}
              className={`rounded-full border px-3 py-1 text-sm ${
                status === "open" ? "border-accent text-accent" : "border-border text-muted"
              }`}
            >
              open {compactNumber(summary.open_nodes)}
            </Link>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface px-4 py-3">
            <p className="text-sm text-muted">
              Showing {compactNumber(page.items.length)} of {compactNumber(page.total)}
            </p>
            <div className="flex gap-2 text-sm">
              {skip > 0 ? (
                <Link
                  href={hrefWith({
                    source_book_id: sourceBookId,
                    status,
                    node_type: nodeType,
                    risk,
                    q,
                    skip: Math.max(0, skip - limit),
                    limit,
                  })}
                  className="rounded-md border border-border px-3 py-1 text-accent hover:border-accent"
                >
                  Previous
                </Link>
              ) : null}
              {skip + limit < page.total ? (
                <Link
                  href={hrefWith({
                    source_book_id: sourceBookId,
                    status,
                    node_type: nodeType,
                    risk,
                    q,
                    skip: skip + limit,
                    limit,
                  })}
                  className="rounded-md border border-border px-3 py-1 text-accent hover:border-accent"
                >
                  Next
                </Link>
              ) : null}
            </div>
          </div>

          {page.items.length ? (
            <div className="space-y-3">
              {page.items.map((item) => (
                <AuditItem key={`${item.node_id}-${item.status}`} item={item} />
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-border bg-surface p-8 text-center text-muted">
              No matching nodes.
            </div>
          )}
        </div>

        <aside className="space-y-4">
          <section className="rounded-lg border border-border bg-surface p-4">
            <h2 className="font-serif text-lg font-semibold text-accent">Node Types</h2>
            <div className="mt-3 space-y-2">
              {nodeTypeRows(summary).map((row) => (
                <Link
                  key={`${row.node_type}-${row.status}`}
                  href={hrefWith({
                    source_book_id: sourceBookId,
                    status: row.status,
                    node_type: row.node_type,
                    risk,
                    q,
                    limit,
                  })}
                  className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2 text-sm hover:border-accent"
                >
                  <span>{row.node_type}</span>
                  <span className="text-muted">
                    {statusLabel(row.status)} · {compactNumber(row.total)}
                  </span>
                </Link>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-border bg-surface p-4">
            <h2 className="font-serif text-lg font-semibold text-accent">Top Methods</h2>
            <div className="mt-3 space-y-2">
              {summary.method_counts.slice(0, 16).map((row) => (
                <div
                  key={`${row.method ?? "none"}-${row.status}`}
                  className="flex items-center justify-between gap-3 border-b border-border/60 pb-2 text-sm last:border-b-0 last:pb-0"
                >
                  <span className="truncate">{row.method ?? "none"}</span>
                  <span className="shrink-0 text-muted">
                    {statusLabel(row.status)} · {compactNumber(row.total)}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </section>
    </main>
  );
}
