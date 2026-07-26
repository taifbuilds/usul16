import { fetchApi } from "@/lib/api/client";
import type { TopicHadithPage, TopicSummary } from "@/lib/api/types";

export async function getTopics(params: {
  q?: string;
  kind?: "kitab" | "chapter" | "mood" | "life" | "practice" | "virtue" | "belief" | "person";
  limit?: number;
} = {}): Promise<TopicSummary[]> {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.kind) query.set("kind", params.kind);
  query.set("limit", String(params.limit ?? 100));
  return fetchApi<TopicSummary[]>(`/topics?${query.toString()}`, {
    next: { revalidate: 60 },
  });
}

export async function getTopicHadiths(
  slug: string,
  params: { skip?: number; limit?: number } = {},
): Promise<TopicHadithPage> {
  const query = new URLSearchParams({
    skip: String(params.skip ?? 0),
    limit: String(params.limit ?? 50),
  });
  return fetchApi<TopicHadithPage>(
    `/topics/${encodeURIComponent(slug)}/hadiths?${query.toString()}`,
    { cache: "no-store" },
  );
}
