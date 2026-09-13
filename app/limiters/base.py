from abc import ABC, abstractmethod
from redis.asyncio import Redis


class RateLimiterStrategy(ABC):

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        key: unique identifier for the client, e.g. f"ratelimit:{user_id}"
        limit: max requests allowed in the window
        window_seconds: size of the window in seconds

        Return True if the request should be ALLOWED, False if it should be
        rejected with a 429.
        """
        raise NotImplementedError
