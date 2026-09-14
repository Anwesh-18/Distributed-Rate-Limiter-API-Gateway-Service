from redis.asyncio import Redis

class CircuitBreaker:
    def __init__(self, redis_client: Redis,failure_threshold: int = 5, cooldown_seconds: int = 30):
        self.redis = redis_client
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

    async def _get_state(self,target:str) -> dict:
        data = await self.redis.hgetall(target)
        return {
            "state" : data.get("state","CLOSED"),
            "failure_count": int(data.get("failure_count",0)),
            "opened_at": float(data.get("opened_at",0)),
        }

    async def can_attempt(self,target: str) -> bool:
        import time
        current = await self._get_state(target)

        if current["state"] == "OPEN":
            if time.time() - current["opened_at"] >= self.cooldown_seconds:
                await self.redis.hset(target,mapping={"state":"HALF_OPEN"})
                return True
            else:
                return False

        return True

    async def record_success(self, target : str) -> None:
        current = await self._get_state(target)

        if current["state"] == "HALF_OPEN":
            await self.redis.hset(target,mapping={"state": "CLOSED","failure_count":0})

    async def record_failure(self, target : str) -> None:
        import time
        await self.redis.hincrby(target,"failure_count",1)
        current = await self._get_state(target)

        if (current["state"] == "HALF_OPEN") or (current["state"] == "CLOSED" and current["failure_count"] >= self.failure_threshold):
            await self.redis.hset(target,mapping={"state": "OPEN","opened_at":time.time()})
