import { search } from "@/lib/api/search";
import { SearchResultCard } from "@/components/search/SearchResultCard";
import { EmptyState } from "@/components/ui/EmptyState";

export const dynamic = "force-dynamic";

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams;
  const query = q?.trim() ?? "";

  if (!query) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-14 sm:px-6">
        <EmptyState title="Search the library" description="Type a word or phrase into the search box above." />
      </div>
    );
  }

  const response = await search(query, 20);

  return (
    <div className="mx-auto max-w-2xl px-4 py-14 sm:px-6">
      <h1 className="font-serif text-3xl">
        {response.count} result{response.count === 1 ? "" : "s"} for{" "}
        <span className="text-accent">&ldquo;{response.query}&rdquo;</span>
      </h1>

      {response.results.length === 0 ? (
        <div className="mt-6">
          <EmptyState
            title="No matches in the currently digitized text"
            description={'Most of the catalog isn’t full-text digitized yet — try a term from one of the books under “Available to read”.'}
          />
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {response.results.map((result) => (
            <SearchResultCard key={result.page.id} result={result} />
          ))}
        </div>
      )}
    </div>
  );
}
