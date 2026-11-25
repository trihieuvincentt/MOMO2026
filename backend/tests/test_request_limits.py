import threading
import time

import pytest

from backend.app.services.request_limits import (
    AnalysisConcurrencyGate,
    RateLimitExceeded,
    SlidingWindowRateLimiter,
)


def test_sliding_window_allows_limit_then_returns_retry_delay():
    now = [10.0]
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=30, clock=lambda: now[0])

    limiter.check("peer-a")
    limiter.check("peer-a")
    with pytest.raises(RateLimitExceeded) as error:
        limiter.check("peer-a")
    assert error.value.retry_after_seconds == 30

    now[0] += 31
    limiter.check("peer-a")


def test_rate_limit_is_isolated_between_clients():
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60, clock=lambda: 5.0)
    limiter.check("peer-a")
    limiter.check("peer-b")


def test_concurrency_gate_rejects_when_capacity_is_exhausted():
    gate = AnalysisConcurrencyGate(max_concurrent=1, wait_seconds=0.01)
    entered = threading.Event()
    release = threading.Event()

    def blocking():
        entered.set()
        release.wait(timeout=2)
        return "done"

    worker = threading.Thread(target=lambda: gate.run(blocking))
    worker.start()
    assert entered.wait(timeout=1)
    try:
        with pytest.raises(RateLimitExceeded):
            gate.run(lambda: "second")
    finally:
        release.set()
        worker.join(timeout=2)


def test_concurrency_gate_releases_capacity_after_failure():
    gate = AnalysisConcurrencyGate(max_concurrent=1)

    with pytest.raises(RuntimeError):
        gate.run(lambda: (_ for _ in ()).throw(RuntimeError("failed")))

    assert gate.run(lambda: "available") == "available"
