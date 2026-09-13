from app.limiters.base import RateLimiterStrategy


class SlidingWindowLimiter(RateLimiterStrategy):

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        pass
