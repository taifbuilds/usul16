import { ApiError, fetchApi } from "@/lib/api/client";
import type {
  BookRead,
  BookSummary,
  CorpusStatusResponse,
  ChapterSummary,
  HadithSplitAudit,
  HadithSplitReviewItem,
  HadithSplitReviewStats,
  HadithChainsRead,
  HadithCommentaryRead,
  HadithRead,
  KitabSummary,
  ThaqalaynChapterSummary,
  NarratorDetailRead,
  NarratorDirectoryPage,
  NarratorHadithAppearancePage,
  NarratorTransmissionEdgesRead,
  PageIndexEntry,
  PageRead,
  PersonResolutionAuditPage,
  PersonResolutionAuditSummary,
  PersonResolutionDecisionSummary,
  TransmissionEdgeEvidenceRead,
  TransmissionGraphRead,
  TransmissionPathsRead,
} from "@/lib/api/types";

export async function getCorpusStatus(): Promise<CorpusStatusResponse> {
  return fetchApi<CorpusStatusResponse>("/corpus-status", { next: { revalidate: 300 } });
}

export async function getBooks(params: {
  skip?: number;
  limit?: number;
  hasContent?: boolean;
} = {}): Promise<BookSummary[]> {
  const query = new URLSearchParams();
  if (params.skip) query.set("skip", String(params.skip));
  query.set("limit", String(params.limit ?? 50));
  if (params.hasContent !== undefined) query.set("has_content", String(params.hasContent));
  return fetchApi<BookSummary[]>(`/books?${query.toString()}`);
}

export async function getBook(bookId: number): Promise<BookRead | null> {
  try {
    return await fetchApi<BookRead>(`/books/${bookId}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

// 5000 matches the crawler's own --max-pages-per-volume safety cap
// (eshia_research/crawler/jobs.py) — confirmed against real data that 500
// (the original assumption here) was too low: al-Kafi vol. 1 alone has 567
// pages, and other Tier 1 volumes run past 900.
const MAX_PAGES_PER_VOLUME = 5000;

export async function getBookPages(
  bookId: number,
  params: { volume?: number; limit?: number } = {}
): Promise<PageRead[]> {
  const query = new URLSearchParams();
  if (params.volume !== undefined) query.set("volume", String(params.volume));
  query.set("limit", String(params.limit ?? MAX_PAGES_PER_VOLUME));
  return fetchApi<PageRead[]>(`/books/${bookId}/pages?${query.toString()}`);
}

export async function getBookPageIndex(
  bookId: number,
  params: { volume?: number } = {}
): Promise<PageIndexEntry[]> {
  const query = new URLSearchParams();
  if (params.volume !== undefined) query.set("volume", String(params.volume));
  return fetchApi<PageIndexEntry[]>(`/books/${bookId}/page-index?${query.toString()}`, {
    next: { revalidate: 60 },
  });
}

export async function getBookHadiths(
  bookId: number,
  params: { volume?: number; page?: number; skip?: number; limit?: number } = {}
): Promise<HadithRead[]> {
  const query = new URLSearchParams();
  if (params.volume !== undefined) query.set("volume", String(params.volume));
  if (params.page !== undefined) query.set("page", String(params.page));
  if (params.skip) query.set("skip", String(params.skip));
  query.set("limit", String(params.limit ?? 200));
  return fetchApi<HadithRead[]>(`/books/${bookId}/hadiths?${query.toString()}`, {
    cache: "no-store",
  });
}

export async function getBookChapters(bookId: number): Promise<ChapterSummary[]> {
  return fetchApi<ChapterSummary[]>(`/books/${bookId}/chapters`, {
    next: { revalidate: 60 },
  });
}

export async function getChapterHadiths(
  bookId: number,
  chapterIndex: number
): Promise<HadithRead[] | null> {
  try {
    return await fetchApi<HadithRead[]>(`/books/${bookId}/chapters/${chapterIndex}/hadiths`, {
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getBookKitabs(bookId: number): Promise<KitabSummary[]> {
  return fetchApi<KitabSummary[]>(`/books/${bookId}/kitabs`, {
    next: { revalidate: 300 },
  });
}

// `volume` disambiguates the kitab: kitab ids restart every printed volume, so
// without it the API merges several unrelated kitabs that share a number.
export async function getKitabChapters(
  bookId: number,
  kitabId: string,
  volume?: number
): Promise<ThaqalaynChapterSummary[] | null> {
  const suffix = volume === undefined ? "" : `?volume=${volume}`;
  try {
    return await fetchApi<ThaqalaynChapterSummary[]>(
      `/books/${bookId}/kitabs/${encodeURIComponent(kitabId)}/chapters${suffix}`,
      { next: { revalidate: 300 } }
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getKitabChapterHadiths(
  bookId: number,
  kitabId: string,
  chapterId: number,
  volume?: number
): Promise<HadithRead[] | null> {
  const suffix = volume === undefined ? "" : `?volume=${volume}`;
  try {
    return await fetchApi<HadithRead[]>(
      `/books/${bookId}/kitabs/${encodeURIComponent(kitabId)}/chapters/${chapterId}/hadiths${suffix}`,
      { cache: "no-store" }
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getHadith(publicId: string): Promise<HadithRead | null> {
  try {
    return await fetchApi<HadithRead>(`/hadiths/${encodeURIComponent(publicId)}`, {
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getHadithChains(publicId: string): Promise<HadithChainsRead | null> {
  try {
    return await fetchApi<HadithChainsRead>(`/hadiths/${encodeURIComponent(publicId)}/chains`, {
      next: { revalidate: 60 },
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getHadithCommentaries(
  publicId: string
): Promise<HadithCommentaryRead[] | null> {
  try {
    return await fetchApi<HadithCommentaryRead[]>(
      `/hadiths/${encodeURIComponent(publicId)}/commentaries`,
      { cache: "no-store" }
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getNarrator(narratorId: number): Promise<NarratorDetailRead | null> {
  try {
    return await fetchApi<NarratorDetailRead>(`/narrators/${narratorId}`, {
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getNarratorHadithAppearances(
  narratorId: number,
  params: { sourceBookId?: string; skip?: number; limit?: number } = {}
): Promise<NarratorHadithAppearancePage | null> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  if (params.skip) query.set("skip", String(params.skip));
  query.set("limit", String(params.limit ?? 120));
  try {
    return await fetchApi<NarratorHadithAppearancePage>(
      `/narrators/${narratorId}/hadith-appearances?${query.toString()}`,
      { next: { revalidate: 60 } }
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getNarratorTransmissionEdges(
  narratorId: number,
  params: { sourceBookId?: string; limit?: number; sampleLimit?: number } = {}
): Promise<NarratorTransmissionEdgesRead | null> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  query.set("limit", String(params.limit ?? 50));
  query.set("sample_limit", String(params.sampleLimit ?? 5));
  try {
    return await fetchApi<NarratorTransmissionEdgesRead>(
      `/narrators/${narratorId}/transmission-edges?${query.toString()}`,
      { cache: "no-store" }
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getHadithSplitReviewStats(params: {
  sourceBookId?: string;
} = {}): Promise<HadithSplitReviewStats> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  return fetchApi<HadithSplitReviewStats>(`/hadith-split-reviews/stats?${query.toString()}`, {
    cache: "no-store",
  });
}

export async function getHadithSplitReviewQueue(params: {
  sourceBookId?: string;
  status?: "all" | "unreviewed" | "approved" | "needs_review" | "rejected";
  flag?: string | null;
  suspiciousOnly?: boolean;
  skip?: number;
  limit?: number;
} = {}): Promise<HadithSplitReviewItem[]> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  if (params.status) query.set("status", params.status);
  if ("flag" in params && params.flag) query.set("flag", params.flag);
  if (params.suspiciousOnly !== undefined) {
    query.set("suspicious_only", String(params.suspiciousOnly));
  }
  if (params.skip) query.set("skip", String(params.skip));
  query.set("limit", String(params.limit ?? 25));
  return fetchApi<HadithSplitReviewItem[]>(`/hadith-split-reviews/queue?${query.toString()}`, {
    cache: "no-store",
  });
}

export async function getHadithSplitAudit(params: {
  sourceBookId?: string;
} = {}): Promise<HadithSplitAudit> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  return fetchApi<HadithSplitAudit>(`/hadith-split-reviews/audit?${query.toString()}`, {
    cache: "no-store",
  });
}

export async function getHadithSplitReviewItem(
  publicId: string
): Promise<HadithSplitReviewItem | null> {
  try {
    return await fetchApi<HadithSplitReviewItem>(
      `/hadith-split-reviews/${encodeURIComponent(publicId)}`,
      { cache: "no-store" }
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getPersonResolutionAuditSummary(params: {
  sourceBookId?: string;
} = {}): Promise<PersonResolutionAuditSummary> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  return fetchApi<PersonResolutionAuditSummary>(
    `/person-resolution-audit/summary?${query.toString()}`,
    { cache: "no-store" }
  );
}

export async function getPersonResolutionAuditQueue(params: {
  sourceBookId?: string;
  status?: string;
  nodeType?: string | null;
  risk?: string | null;
  machineDecision?: string | null;
  q?: string | null;
  adminReviewed?: boolean;
  skip?: number;
  limit?: number;
} = {}): Promise<PersonResolutionAuditPage> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  if (params.status) query.set("status", params.status);
  if (params.nodeType) query.set("node_type", params.nodeType);
  if (params.risk) query.set("risk", params.risk);
  if (params.machineDecision) query.set("machine_decision", params.machineDecision);
  if (params.q) query.set("q", params.q);
  if (params.adminReviewed) query.set("admin_reviewed", "true");
  if (params.skip) query.set("skip", String(params.skip));
  query.set("limit", String(params.limit ?? 50));
  return fetchApi<PersonResolutionAuditPage>(
    `/person-resolution-audit/queue?${query.toString()}`,
    { cache: "no-store" }
  );
}

export async function getPersonResolutionDecisionSummary(params: {
  sourceBookId?: string;
  reviewer?: string;
} = {}): Promise<PersonResolutionDecisionSummary> {
  const query = new URLSearchParams();
  if (params.sourceBookId) query.set("source_book_id", params.sourceBookId);
  if (params.reviewer) query.set("reviewer", params.reviewer);
  return fetchApi<PersonResolutionDecisionSummary>(
    `/person-resolution-decisions/summary?${query.toString()}`,
    { cache: "no-store" }
  );
}

export async function getPage(pageId: number): Promise<PageRead | null> {
  try {
    return await fetchApi<PageRead>(`/pages/${pageId}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function getNarratorDirectory(params: {
  query?: string;
  limit?: number;
  offset?: number;
  sort?: "charted" | "name";
} = {}): Promise<NarratorDirectoryPage> {
  const query = new URLSearchParams();
  if (params.query) query.set("query", params.query);
  query.set("limit", String(params.limit ?? 40));
  query.set("offset", String(params.offset ?? 0));
  if (params.sort) query.set("sort", params.sort);
  return fetchApi<NarratorDirectoryPage>(`/narrators?${query.toString()}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(20_000),
  });
}

export async function getTransmissionGraph(params: {
  sourceBookId?: string;
  books?: string[];
  minCount?: number;
  maxNodes?: number;
  quality?: boolean;
  includeUncertain?: boolean;
} = {}): Promise<TransmissionGraphRead> {
  const query = new URLSearchParams();
  if (params.books && params.books.length) query.set("books", params.books.join(","));
  else query.set("source_book_id", params.sourceBookId ?? "11005");
  query.set("min_count", String(params.minCount ?? 2));
  query.set("max_nodes", String(params.maxNodes ?? 500));
  if (params.quality) query.set("quality", "1");
  if (params.includeUncertain) query.set("include_uncertain", "1");
  // no-store: the graph must reflect resolver re-runs and review corrections
  // immediately (the backend TTL-caches the heavy aggregation itself).
  return fetchApi<TransmissionGraphRead>(`/transmission-graph?${query.toString()}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(45_000),
  });
}

export async function getTransmissionPaths(params: {
  fromPerson: number;
  toPerson: number;
  books?: string[];
  maxLen?: number;
  k?: number;
}): Promise<TransmissionPathsRead> {
  const query = new URLSearchParams();
  query.set("from_person", String(params.fromPerson));
  query.set("to_person", String(params.toPerson));
  if (params.books && params.books.length) query.set("books", params.books.join(","));
  if (params.maxLen) query.set("max_len", String(params.maxLen));
  if (params.k) query.set("k", String(params.k));
  return fetchApi<TransmissionPathsRead>(`/transmission-graph/paths?${query.toString()}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(30_000),
  });
}

export async function getTransmissionEdgeEvidence(params: {
  sourcePersonId: number;
  targetPersonId: number;
  sourceBookId?: string;
  books?: string[];
  limit?: number;
}): Promise<TransmissionEdgeEvidenceRead> {
  const query = new URLSearchParams();
  query.set("source_person_id", String(params.sourcePersonId));
  query.set("target_person_id", String(params.targetPersonId));
  if (params.books && params.books.length) query.set("books", params.books.join(","));
  else query.set("source_book_id", params.sourceBookId ?? "11005");
  query.set("limit", String(params.limit ?? 25));
  return fetchApi<TransmissionEdgeEvidenceRead>(
    `/transmission-graph/edge-evidence?${query.toString()}`,
    { cache: "no-store" }
  );
}
