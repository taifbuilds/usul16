import time

from eshia_research.crawler.client import AdaptiveThrottle


def test_no_cooldown_when_no_errors_recorded():
    throttle = AdaptiveThrottle(window=5, error_threshold=0.3, cooldown_seconds=5.0)
    for _ in range(10):
        throttle.record(was_retryable_error=False)

    start = time.monotonic()
    throttle.wait_if_needed()
    assert time.monotonic() - start < 0.05


def test_cooldown_triggers_once_error_rate_crosses_threshold():
    throttle = AdaptiveThrottle(window=4, error_threshold=0.5, cooldown_seconds=0.2)
    # 2/4 errors = 50% >= 50% threshold -> cooldown engaged
    throttle.record(was_retryable_error=True)
    throttle.record(was_retryable_error=False)
    throttle.record(was_retryable_error=True)
    throttle.record(was_retryable_error=False)

    start = time.monotonic()
    throttle.wait_if_needed()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.15  # cooldown actually delayed the caller


def test_cooldown_does_not_trigger_below_threshold():
    throttle = AdaptiveThrottle(window=4, error_threshold=0.5, cooldown_seconds=5.0)
    # 1/4 errors = 25% < 50% threshold -> no cooldown
    throttle.record(was_retryable_error=True)
    throttle.record(was_retryable_error=False)
    throttle.record(was_retryable_error=False)
    throttle.record(was_retryable_error=False)

    start = time.monotonic()
    throttle.wait_if_needed()
    assert time.monotonic() - start < 0.05


def test_sustained_low_error_rate_never_triggers_cooldown():
    throttle = AdaptiveThrottle(window=4, error_threshold=0.5, cooldown_seconds=5.0)
    # 25% error rate, sustained well below the 50% threshold, across many
    # more calls than the window size — a true sliding window should never
    # see a 4-in-a-row error run here.
    pattern = [True, False, False, False]
    for _ in range(20):
        for outcome in pattern:
            throttle.record(was_retryable_error=outcome)

    start = time.monotonic()
    throttle.wait_if_needed()
    assert time.monotonic() - start < 0.05


def test_cooldown_expires_naturally_after_cooldown_seconds():
    throttle = AdaptiveThrottle(window=4, error_threshold=0.5, cooldown_seconds=0.1)
    for _ in range(4):
        throttle.record(was_retryable_error=True)

    time.sleep(0.15)  # let the cooldown elapse on its own
    start = time.monotonic()
    throttle.wait_if_needed()
    assert time.monotonic() - start < 0.05


def test_cooldown_is_shared_across_multiple_record_calls_from_different_threads():
    # Simulates what concurrent workers do: many threads call record(); once
    # the shared error rate crosses the threshold, *every* caller's next
    # wait_if_needed() should block, not just the one that tipped it over.
    throttle = AdaptiveThrottle(window=10, error_threshold=0.5, cooldown_seconds=0.2)
    for _ in range(10):
        throttle.record(was_retryable_error=True)

    start = time.monotonic()
    throttle.wait_if_needed()
    assert time.monotonic() - start >= 0.15
