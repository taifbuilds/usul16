const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Thin fetch wrapper for the eshia-research FastAPI backend. Every route it
 * calls is public/read-only (no auth exists), so this stays deliberately
 * simple — no token handling, no client-side cache library. */
const API_TIMEOUT_MS = 15_000;

export async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const next =
    init?.cache === "no-store"
      ? undefined
      : { revalidate: 60, ...(init as { next?: { revalidate?: number | false } } | undefined)?.next };
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: init?.signal ?? AbortSignal.timeout(API_TIMEOUT_MS),
      ...(next ? { next } : {}),
    });
  } catch (error) {
    const message = error instanceof DOMException && error.name === "TimeoutError"
      ? "The research service took too long to respond."
      : "The research service is temporarily unavailable.";
    throw new ApiError(503, message);
  }

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") message = body.detail;
    } catch {
      // body wasn't JSON — fall back to statusText
    }
    throw new ApiError(response.status, message);
  }

  return response.json() as Promise<T>;
}
