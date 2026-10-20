import pytest

from about_rag.ratelimit import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_the_limit_then_blocks():
    limiter = RateLimiter(limit=3, window=60, clock=FakeClock())
    assert [limiter.acquire("ip") for _ in range(3)] == [0.0, 0.0, 0.0]
    assert limiter.acquire("ip") > 0


def test_blocked_requests_report_when_the_oldest_hit_expires():
    clock = FakeClock()
    limiter = RateLimiter(limit=2, window=60, clock=clock)
    limiter.acquire("ip")
    clock.now += 10
    limiter.acquire("ip")
    clock.now += 5
    assert limiter.acquire("ip") == pytest.approx(45)  # first hit was 15s ago


def test_window_slides_so_old_hits_stop_counting():
    clock = FakeClock()
    limiter = RateLimiter(limit=2, window=60, clock=clock)
    limiter.acquire("ip")
    limiter.acquire("ip")
    clock.now += 60
    assert limiter.acquire("ip") == 0.0


def test_blocked_requests_are_not_counted():
    clock = FakeClock()
    limiter = RateLimiter(limit=1, window=60, clock=clock)
    limiter.acquire("ip")
    for _ in range(5):
        limiter.acquire("ip")
    clock.now += 60
    assert limiter.acquire("ip") == 0.0


def test_keys_are_limited_independently():
    limiter = RateLimiter(limit=1, window=60, clock=FakeClock())
    assert limiter.acquire("1.1.1.1") == 0.0
    assert limiter.acquire("2.2.2.2") == 0.0
    assert limiter.acquire("1.1.1.1") > 0


def test_idle_keys_are_forgotten():
    clock = FakeClock()
    limiter = RateLimiter(limit=1, window=60, clock=clock)
    for i in range(1024):
        limiter.acquire(f"ip-{i}")
    clock.now += 61
    limiter.acquire("new-ip")
    assert len(limiter) == 1


@pytest.mark.parametrize(("limit", "window"), [(0, 60), (5, 0)])
def test_rejects_non_positive_settings(limit, window):
    with pytest.raises(ValueError):
        RateLimiter(limit=limit, window=window)
