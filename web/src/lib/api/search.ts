import { fetchApi } from "@/lib/api/client";
import type { SearchResponse } from "@/lib/api/types";

export async function search(query: string, limit = 20): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  // Search results change as the crawl progresses, and the query string
  // itself makes each request distinct anyway — no point caching long.
  return fetchApi<SearchResponse>(`/search?${params.toString()}`, { next: { revalidate: 0 } });
}
