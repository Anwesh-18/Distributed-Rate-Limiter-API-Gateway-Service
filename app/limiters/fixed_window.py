from app.limiters.base import RateLimiterStrategy

class FixedWindowLimiter(RateLimiterStrategy):
  async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
    import time
    current_window = int(time.time() // window_seconds)
    redis_key = f"{key}:{current_window}"

    count = await self.redis.incr(redis_key)

    if count == 1:
      await self.redis.expire(redis_key, window_seconds)

    return count <= limit
