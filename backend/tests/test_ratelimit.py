from jobfit.ratelimit import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_blocks_after_limit_and_recovers_after_window():
    clock = FakeClock()
    limiter = RateLimiter(2, window_seconds=60, clock=clock)
    assert limiter.allow("1.2.3.4")
    assert limiter.allow("1.2.3.4")
    assert not limiter.allow("1.2.3.4")
    assert limiter.allow("5.6.7.8"), "each visitor has their own budget"

    clock.now = 61
    assert limiter.allow("1.2.3.4")


def test_zero_disables_limiting():
    limiter = RateLimiter(0, window_seconds=60)
    assert all(limiter.allow("x") for _ in range(100))
