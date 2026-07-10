import { fetchApi } from "@/lib/api/client";
import type { LibraryStats } from "@/lib/api/types";

export async function getStats(): Promise<LibraryStats> {
  return fetchApi<LibraryStats>("/stats", { next: { revalidate: 300 } });
}
