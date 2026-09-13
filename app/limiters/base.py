from abc import ABC, abstractmethod
from redis.asyncio import Redis


class RateLimiterStrategy(ABC):

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        raise NotImplementedError
