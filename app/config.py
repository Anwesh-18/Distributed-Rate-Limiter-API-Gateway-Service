from pydantic_settings import BaseSettings

class TierLimit:
    def __init__(self, requests: int, window_seconds: int):
        self.requests = requests
        self.window_seconds = window_seconds

class Settings(BaseSettings):
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"

    downstream_url: str = "http://downstream:9000"

    active_algorithm: str = "fixed_window"

    class Config:
        env_file = ".env"

settings = Settings()

TIER_LIMITS = {
    "free": TierLimit(requests=10, window_seconds=60),
    "pro": TierLimit(requests=100, window_seconds=60),
    "enterprise": TierLimit(requests=1000, window_seconds=60),
}
