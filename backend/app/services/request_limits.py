import threading
import time
from collections import deque


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("request rate limit exceeded")


class SlidingWindowRateLimiter:
    """Small per-process sliding-window limiter suitable for a demo instance."""

    def __init__(self, *, max_requests: int = 20, window_seconds: int = 60, clock=time.monotonic) -> None:
        if max_requests < 1 or window_seconds < 1:
            raise ValueError("Rate limit values must be positive")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock
        self._requests: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = self.clock()
        with self._lock:
            timestamps = self._requests.setdefault(key, deque())
            cutoff = now - self.window_seconds
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - timestamps[0])))
                raise RateLimitExceeded(retry_after)
            timestamps.append(now)
            if len(self._requests) > 4096:
                stale = [client for client, events in self._requests.items() if not events or events[-1] <= cutoff]
                for client in stale:
                    self._requests.pop(client, None)


class AnalysisConcurrencyGate:
    """Bound simultaneous website analyses in one application process."""

    def __init__(self, *, max_concurrent: int = 2, wait_seconds: float = 0.25) -> None:
        if max_concurrent < 1 or wait_seconds < 0:
            raise ValueError("Concurrency limits are invalid")
        self._semaphore = threading.BoundedSemaphore(max_concurrent)
        self.wait_seconds = wait_seconds

    def run(self, operation, *args, **kwargs):
        if not self._semaphore.acquire(timeout=self.wait_seconds):
            raise RateLimitExceeded(max(1, int(self.wait_seconds) + 1))
        try:
            return operation(*args, **kwargs)
        finally:
            self._semaphore.release()
