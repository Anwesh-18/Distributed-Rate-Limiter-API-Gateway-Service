import pytest
import fakeredis.aioredis
from app.limiters import FixedWindowLimiter,TokenBucketLimiter,SlidingWindowLimiter
import asyncio

@pytest.fixture
async def redis_client():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)  # decode_response give the python string not the raw data
    yield client
    await client.flushall()

# Fixed_Window_Algorithm
@pytest.mark.asyncio
async def test_fixed_window_allows_up_to_limit(redis_client):
    limiter = FixedWindowLimiter(redis_client)
    key = "ratelimit:test-user"

    for _ in range(5):
        assert await limiter.is_allowed(key, limit=5, window_seconds=60) is True

    assert await limiter.is_allowed(key, limit=5, window_seconds=60) is False


@pytest.mark.asyncio
async def test_fixed_window_different_users_independent(redis_client):
    limiter = FixedWindowLimiter(redis_client)

    for _ in range(3):
        assert await limiter.is_allowed("ratelimit:user-a", limit=3, window_seconds=60) is True

    assert await limiter.is_allowed("ratelimit:user-b", limit=3, window_seconds=60) is True

@pytest.mark.asyncio
async def test_fixed_window_resets_after_window_expires(redis_client):
    limiter = FixedWindowLimiter(redis_client)
    key = "ratelimit:test-user"

    for _ in range(3):
        assert await limiter.is_allowed(key, limit= 3, window_seconds=1) is True

    assert await limiter.is_allowed(key, limit= 3, window_seconds=1) is False

    await asyncio.sleep(1.1)

    assert await limiter.is_allowed(key, limit= 3, window_seconds=1) is True


# Token_Bucket_Algorithm
@pytest.mark.asyncio
async def test_token_bucket_allows_up_to_limit(redis_client):
    limiter = TokenBucketLimiter(redis_client)
    key = "ratelimit:test-user"

    for _ in range(5):
        assert await limiter.is_allowed(key, limit=5, window_seconds=60) is True

    assert await limiter.is_allowed(key, limit=5, window_seconds=60) is False


@pytest.mark.asyncio
async def test_token_bucket_different_users_independent(redis_client):
    limiter = TokenBucketLimiter(redis_client)

    for _ in range(3):
        assert await limiter.is_allowed("ratelimit:user-a", limit=3, window_seconds=60) is True

    assert await limiter.is_allowed("ratelimit:user-b", limit=3, window_seconds=60) is True

@pytest.mark.asyncio
async def test_token_bucket_resets_after_window_expires(redis_client):
    limiter = TokenBucketLimiter(redis_client)
    key = "ratelimit:test-user"

    for _ in range(3):
        assert await limiter.is_allowed(key, limit= 3, window_seconds=1) is True

    assert await limiter.is_allowed(key, limit= 3, window_seconds=1) is False

    await asyncio.sleep(1.1)

    assert await limiter.is_allowed(key, limit= 3, window_seconds=1) is True


# Sliding_Window_Algorithm
@pytest.mark.asyncio
async def test_sliding_window_allows_up_to_limit(redis_client):
    limiter = SlidingWindowLimiter(redis_client)
    key = "ratelimit:test-user"

    for _ in range(5):
        assert await limiter.is_allowed(key, limit=5, window_seconds=60) is True

    assert await limiter.is_allowed(key, limit=5, window_seconds=60) is False


@pytest.mark.asyncio
async def test_sliding_window_different_users_independent(redis_client):
    limiter = SlidingWindowLimiter(redis_client)

    for _ in range(3):
        assert await limiter.is_allowed("ratelimit:user-a", limit=3, window_seconds=60) is True

    assert await limiter.is_allowed("ratelimit:user-b", limit=3, window_seconds=60) is True

@pytest.mark.asyncio
async def test_sliding_window_resets_after_window_expires(redis_client):
    limiter = SlidingWindowLimiter(redis_client)
    key = "ratelimit:test-user"

    for _ in range(3):
        assert await limiter.is_allowed(key, limit= 3, window_seconds=1) is True

    assert await limiter.is_allowed(key, limit= 3, window_seconds=1) is False

    await asyncio.sleep(1.1)

    assert await limiter.is_allowed(key, limit= 3, window_seconds=1) is True


