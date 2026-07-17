import { search } from "@/lib/api/search";
import { SearchBox } from "@/components/nav/SearchBox";
import { SearchResultCard } from "@/components/search/SearchResultCard";
import { EmptyState } from "@/components/ui/EmptyState";
import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Search the hadith corpus",
  description: "Search digitised Arabic source text and available public English translations.",
  alternates: { canonical: "/search" },
};

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams;
  const query = q?.trim() ?? "";
  const response = query ? await search(query, 20) : null;

  return (
    <div className="mx-auto max-w-[90rem] px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
      <header className="grid gap-10 border-b border-border pb-10 lg:grid-cols-[minmax(0,1fr)_18rem] lg:items-end">
        <div>
          <p className="text-sm font-semibold text-accent">Find in the corpus</p>
          <h1 className="mt-3 font-serif text-5xl font-semibold tracking-[-0.025em] sm:text-6xl">Search without losing the source.</h1>
          <p className="mt-4 max-w-2xl leading-7 text-muted">Search digitised Arabic and available public English translations, then open the source page or stable hadith record.</p>
          <div className="mt-7 max-w-3xl"><SearchBox defaultValue={query} size="lg" /></div>
        </div>
        <aside className="border-t border-border pt-5 text-sm lg:border-l lg:border-t-0 lg:pl-6">
          <p className="font-semibold text-foreground">Search notes</p>
          <ul className="mt-3 space-y-2 leading-6 text-muted">
            <li>Arabic gives the closest source-text matches.</li>
            <li>Try a shorter root or spelling variant.</li>
            <li>Each result opens in printed-page context.</li>
          </ul>
        </aside>
      </header>

      {!response ? (
        <div className="mt-10 max-w-4xl"><EmptyState title="Enter a word or phrase" description="Begin with an Arabic phrase, an English concept, or a collection title." /></div>
      ) : (
        <section className="mt-10 grid gap-8 lg:grid-cols-[12rem_minmax(0,1fr)]">
          <div>
            <p className="text-sm font-semibold text-foreground">Results</p>
            <p className="mt-1 text-sm text-muted">Showing {response.count} {response.count === 1 ? "result" : "results"}</p>
          </div>
          <div>
          <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-border pb-5">
            <h2 className="font-serif text-2xl font-semibold">“{response.query}”</h2>
            <p className="text-xs font-medium text-muted">Ordered by source occurrence</p>
          </div>
          {response.results.length === 0 ? (
            <div className="mt-6"><EmptyState title="No matches in the digitised text" description="Try a shorter term, a spelling variant, or another word from the source." /></div>
          ) : (
            <div className="divide-y divide-border border-b border-border">
              {response.results.map((result, index) => <SearchResultCard key={`${result.match_type}-${result.hadith_public_id ?? result.page.id}-${index}`} result={result} />)}
            </div>
          )}
          </div>
        </section>
      )}
    </div>
  );
}
