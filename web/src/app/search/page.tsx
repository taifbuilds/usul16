import { search } from "@/lib/api/search";
import { SearchBox } from "@/components/nav/SearchBox";
import { SearchResultCard } from "@/components/search/SearchResultCard";
import { EmptyState } from "@/components/ui/EmptyState";
import type { Metadata } from "next";
import Link from "next/link";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Search the hadith corpus",
  description: "Search Arabic source text, translations, topics, and hashtags.",
  alternates: { canonical: "/search" },
};

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams;
  const query = q?.trim() ?? "";
  const response = query ? await search(query, 20) : null;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <header className="border-b border-border pb-8">
        <p className="text-sm font-semibold text-accent">Find in the corpus</p>
        <h1 className="mt-2 max-w-4xl font-serif text-4xl font-semibold leading-tight sm:text-5xl">Search without losing the source.</h1>
        <p className="mt-3 max-w-2xl leading-7 text-muted">Search Arabic, available English translations, topics, or hashtags, then open the stable hadith record.</p>
        <div className="mt-6 max-w-4xl"><SearchBox defaultValue={query} size="lg" /></div>
        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
          <Link href="/topics" className="inline-flex min-h-10 items-center font-semibold text-accent hover:underline">
            Browse hadith topics
          </Link>
          <span className="text-muted">Try a mood, practice, person, or Arabic phrase.</span>
        </div>
        <details className="group mt-4 max-w-4xl border-y border-border text-sm">
          <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-4 py-2 font-semibold text-foreground">
            Search guidance
            <span aria-hidden className="text-muted transition-transform duration-200 group-open:rotate-180">⌄</span>
          </summary>
          <ul className="grid gap-x-8 gap-y-2 border-t border-border py-4 leading-6 text-muted sm:grid-cols-2">
            <li>Arabic gives the closest source-text matches.</li>
            <li>Every result opens in printed-page context.</li>
            <li>Search topics such as knowledge or prayer.</li>
            <li>Hashtags work directly, for example #seeking-knowledge.</li>
          </ul>
        </details>
      </header>

      {!response ? (
        <div className="mt-8 max-w-4xl"><EmptyState title="Enter a word or phrase" description="Begin with an Arabic phrase, an English concept, or a collection title." /></div>
      ) : (
        <section className="mt-8" aria-labelledby="results-heading">
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-border pb-4">
            <div>
              <p className="text-xs font-semibold text-muted">{response.count} {response.count === 1 ? "result" : "results"}</p>
              <h2 id="results-heading" className="mt-1 font-serif text-2xl font-semibold">“{response.query}”</h2>
            </div>
            <p className="text-xs font-medium text-muted">The collections first, then printed order</p>
          </div>
          {response.results.length === 0 ? (
            <div className="mt-6"><EmptyState title="No matches in the digitised text" description="Try a shorter term, a spelling variant, or another word from the source." /></div>
          ) : (
            <div className="divide-y divide-border border-b border-border">
              {response.results.map((result, index) => <SearchResultCard key={`${result.match_type}-${result.hadith_public_id ?? result.page.id}-${index}`} result={result} />)}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
