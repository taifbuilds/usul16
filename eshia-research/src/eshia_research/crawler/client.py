"""Polite, retrying HTTP client used by the crawler.

Three concerns are kept separate:
  - `PoliteClient` handles per-request mechanics: delay between requests,
    timeouts, and retry/backoff on transient errors. Thread-safe so it can
    be shared across concurrent workers.
  - `AdaptiveThrottle` is a shared circuit breaker: when running with
    concurrency, individual per-request delays stop being a meaningful
    safety net (8 workers each "waiting politely" is still 8x the load).
    This watches the recent error rate across *all* workers and forces a
    shared cooldown if the target looks like it's struggling, so going fast
    degrades gracefully instead of escalating into a de facto DoS.
  - `Checkpoint` handles crawl-level resumability: which URLs have already
    been fetched successfully in a previous (possibly interrupted) run, so a
    re-run of the same crawl command can skip them.
"""

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from eshia_research.config import Settings, get_settings

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class CrawlError(Exception):
    """Raised when a URL could not be fetched after exhausting retries."""

    def __init__(self, url: str, message: str, http_status: int | None = None):
        super().__init__(message)
        self.url = url
        self.http_status = http_status


@dataclass
class Checkpoint:
    """Tracks which URLs have already been crawled successfully.

    Stored as a flat JSON file: {"<url>": "<checksum>"}. Resuming a crawl just
    means skipping any URL already present here.

    mark_done is called from every concurrent crawl worker thread (see
    crawl_full_library/crawl_book_concurrent), so mutating `_done` and
    serializing it to JSON must happen under a lock — without one, one
    thread's json.dumps can be mid-iteration over `_done` while another
    thread adds a key, raising "dictionary changed size during iteration"
    (hit for real on a 71k-page concurrent crawl).
    """

    path: Path
    _done: dict[str, str] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.path.exists():
            self._done = json.loads(self.path.read_text(encoding="utf-8"))

    def is_done(self, url: str) -> bool:
        with self._lock:
            return url in self._done

    def mark_done(self, url: str, checksum: str) -> None:
        with self._lock:
            self._done[url] = checksum
            self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._done, ensure_ascii=False, indent=2), encoding="utf-8")


class AdaptiveThrottle:
    """Shared circuit breaker for concurrent crawling.

    Tracks a sliding window of recent outcomes (retryable-error or not)
    across every worker sharing this instance. Once the error rate in that
    window crosses `error_threshold`, every worker is forced into a shared
    cooldown before its next request — i.e. "going fast" automatically
    backs off the moment the target shows signs of distress, instead of
    every worker independently retrying into the same wall.
    """

    def __init__(self, window: int = 20, error_threshold: float = 0.3, cooldown_seconds: float = 10.0):
        self._lock = threading.Lock()
        self._outcomes: deque[bool] = deque(maxlen=window)
        self._error_threshold = error_threshold
        self._cooldown_seconds = cooldown_seconds
        self._cooldown_until: float = 0.0

    def wait_if_needed(self) -> None:
        with self._lock:
            cooldown_until = self._cooldown_until
        remaining = cooldown_until - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)

    def record(self, was_retryable_error: bool) -> None:
        with self._lock:
            self._outcomes.append(was_retryable_error)
            # Deliberately NOT cleared after tripping: clearing would turn
            # this into non-overlapping batches (re-arm only every `window`
            # calls), which can miss a sustained error run that straddles a
            # batch boundary. Letting the deque's maxlen evict the oldest
            # entry on each append keeps this a true sliding window, so a
            # bad run keeps re-tripping (pushing cooldown_until further out)
            # for as long as it continues.
            if len(self._outcomes) == self._outcomes.maxlen:
                error_rate = sum(self._outcomes) / len(self._outcomes)
                if error_rate >= self._error_threshold:
                    self._cooldown_until = time.monotonic() + self._cooldown_seconds


class PoliteClient:
    """Wraps httpx with a delay, timeout, and bounded retries.

    Retries only fire on RETRYABLE_STATUS_CODES (429/500/502/503/504) or
    network-level errors. Other HTTP statuses (e.g. 404) are returned as-is
    so the caller can decide what to do with them.

    Thread-safe: httpx.Client itself supports concurrent use, and the
    per-request delay bookkeeping here is guarded by a lock, so a single
    PoliteClient (sharing one connection pool, one AdaptiveThrottle, and one
    retry policy) can be handed to multiple worker threads at once.
    """

    def __init__(self, settings: Settings | None = None, throttle: AdaptiveThrottle | None = None):
        self.settings = settings or get_settings()
        self.throttle = throttle
        self._client = httpx.Client(
            headers={"User-Agent": self.settings.crawl_user_agent},
            timeout=self.settings.crawl_timeout_seconds,
            follow_redirects=True,
        )
        self._last_request_at: float | None = None
        self._delay_lock = threading.Lock()

    def __enter__(self) -> "PoliteClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _wait_for_delay(self) -> None:
        with self._delay_lock:
            if self._last_request_at is not None:
                elapsed = time.monotonic() - self._last_request_at
                remaining = self.settings.crawl_delay_seconds - elapsed
                if remaining > 0:
                    time.sleep(remaining)
            self._last_request_at = time.monotonic()

    def get(self, url: str) -> httpx.Response:
        max_retries = self.settings.crawl_max_retries
        attempt = 0
        last_exc: Exception | None = None

        while attempt <= max_retries:
            if self.throttle is not None:
                self.throttle.wait_if_needed()
            self._wait_for_delay()
            try:
                response = self._client.get(url)
            except httpx.HTTPError as exc:
                last_exc = exc
                attempt += 1
                if self.throttle is not None:
                    self.throttle.record(was_retryable_error=True)
                self._backoff(attempt, retry_after=None)
                continue

            is_retryable = response.status_code in RETRYABLE_STATUS_CODES
            if self.throttle is not None:
                self.throttle.record(was_retryable_error=is_retryable)

            if not is_retryable:
                return response

            attempt += 1
            if attempt > max_retries:
                raise CrawlError(
                    url,
                    f"Giving up after {max_retries} retries (last status {response.status_code})",
                    http_status=response.status_code,
                )
            self._backoff(attempt, retry_after=response.headers.get("Retry-After"))

        raise CrawlError(url, f"Request failed: {last_exc}") from last_exc

    def _backoff(self, attempt: int, retry_after: str | None) -> None:
        if retry_after is not None:
            try:
                time.sleep(float(retry_after))
                return
            except ValueError:
                pass
        time.sleep(self.settings.crawl_delay_seconds * (2**attempt))
