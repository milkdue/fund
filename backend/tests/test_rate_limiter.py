import pytest

from app.services.source_rate_limiter import RateLimitExceededError, SlidingWindowRateLimiter


def test_rate_limiter_blocks_after_limit():
    limiter = SlidingWindowRateLimiter(window_seconds=60)
    limiter.acquire_or_raise("eastmoney_nav", limit=2, now=100.0)
    limiter.acquire_or_raise("eastmoney_nav", limit=2, now=110.0)

    with pytest.raises(RateLimitExceededError):
        limiter.acquire_or_raise("eastmoney_nav", limit=2, now=120.0)


def test_rate_limiter_resets_after_window():
    limiter = SlidingWindowRateLimiter(window_seconds=60)
    limiter.acquire_or_raise("eastmoney_search", limit=1, now=100.0)
    limiter.acquire_or_raise("eastmoney_search", limit=1, now=161.0)
