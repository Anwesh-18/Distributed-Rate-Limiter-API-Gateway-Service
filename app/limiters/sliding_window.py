from app.limiters.base import RateLimiterStrategy
import uuid


class SlidingWindowLimiter(RateLimiterStrategy):

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        import time
        now = time.time()
        window_start = now - window_seconds

        await self.redis.zremrangebyscore(key,0,window_start)

        count = await self.redis.zcard(key)

        if count < limit:
            await self.redis.zadd(key,{f"{now}:{uuid.uuid4()}":now})
            await self.redis.expire(key,window_seconds)
            return True

        else:
            return False