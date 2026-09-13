"""
Run with: pytest tests/ -v

fakeredis gives you an in-memory Redis so tests don't need a real Redis
instance running. Once you implement FixedWindowLimiter, this test should
pass as-is.
"""
import pytest
import fakeredis.aioredis
from app.limiters.fixed_window import FixedWindowLimiter


@pytest.fixture
async def redis_client():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()


@pytest.mark.asyncio
async def test_fixed_window_allows_up_to_limit(redis_client):
    limiter = FixedWindowLimiter(redis_client)
    key = "ratelimit:test-user"

    # first 5 requests within limit=5 should all be allowed
    for _ in range(5):
        assert await limiter.is_allowed(key, limit=5, window_seconds=60) is True

    # the 6th should be rejected
    assert await limiter.is_allowed(key, limit=5, window_seconds=60) is False


@pytest.mark.asyncio
async def test_fixed_window_different_users_independent(redis_client):
    limiter = FixedWindowLimiter(redis_client)

    for _ in range(3):
        assert await limiter.is_allowed("ratelimit:user-a", limit=3, window_seconds=60) is True

    # user-b should have their own independent limit, unaffected by user-a
    assert await limiter.is_allowed("ratelimit:user-b", limit=3, window_seconds=60) is True

# TODO once you implement token_bucket.py and sliding_window.py:
# write equivalent tests, plus one specifically testing that token bucket
# allows a burst up to bucket size, and one testing sliding window's
# accuracy right at the window boundary (this is the case fixed window
# gets wrong -- prove your sliding window implementation gets it right).
