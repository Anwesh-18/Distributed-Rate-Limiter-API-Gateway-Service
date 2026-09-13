from redis.asyncio import Redis
from app.config import settings
from app.limiters.base import RateLimiterStrategy
from app.limiters.fixed_window import FixedWindowLimiter
from app.limiters.token_bucket import TokenBucketLimiter
from app.limiters.sliding_window import SlidingWindowLimiter

_STRATEGIES = {
    "fixed_window": FixedWindowLimiter,
    "token_bucket": TokenBucketLimiter,
    "sliding_window": SlidingWindowLimiter,
}


def get_limiter(redis_client: Redis) -> RateLimiterStrategy:
    strategy_cls = _STRATEGIES[settings.active_algorithm]
    return strategy_cls(redis_client)
