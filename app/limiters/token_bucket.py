from app.limiters.base import RateLimiterStrategy


class TokenBucketLimiter(RateLimiterStrategy):

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        import time
        now = time.time()
        data = await self.redis.hmget(key,"tokens","last_refill")
        tokens = float(data[0]) if data[0] else limit
        last_refill = float(data[1]) if data[1] else now

        refill_rate = limit / window_seconds
        elapsed = now - last_refill
        tokens = min(limit, tokens + (elapsed * refill_rate))

        if tokens >= 1:
            tokens -= 1
            allowed = True
        else:
            allowed = False

        await self.redis.hset(key,mapping={"tokens":tokens,"last_refill":last_refill})
        return allowed