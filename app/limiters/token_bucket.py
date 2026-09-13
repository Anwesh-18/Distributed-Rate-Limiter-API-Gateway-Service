from app.limiters.base import RateLimiterStrategy


class TokenBucketLimiter(RateLimiterStrategy):

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        pass
