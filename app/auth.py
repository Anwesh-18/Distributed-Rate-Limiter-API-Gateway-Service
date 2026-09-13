import jwt
from fastapi import Header, HTTPException
from app.config import settings, TIER_LIMITS


class AuthedClient:
    def __init__(self, user_id: str, tier: str):
        self.user_id = user_id
        self.tier = tier
        self.tier_limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])


async def get_current_client(authorization: str = Header(default=None)) -> AuthedClient:

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or UnAuthorized")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    tier = payload.get("tier", "free")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing 'sub'")

    return AuthedClient(user_id=user_id, tier=tier)
