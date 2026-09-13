import httpx
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import Response

from app.config import settings
from app.redis_client import get_redis
from app.auth import get_current_client, AuthedClient
from app.limiters import get_limiter

app = FastAPI(title="Rate Limiter Gateway")


@app.get("/health")
async def health():
    return {"status": "ok", "active_algorithm": settings.active_algorithm}


@app.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request, client: AuthedClient = Depends(get_current_client)):
    redis_client = get_redis()
    limiter = get_limiter(redis_client)

    rate_key = f"ratelimit:{client.user_id}"
    allowed = await limiter.is_allowed(
        key=rate_key,
        limit=client.tier_limit.requests,
        window_seconds=client.tier_limit.window_seconds,
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for tier '{client.tier}'. Try again shortly.",
        )

    
    downstream_url = f"{settings.downstream_url}/{path}"
    body = await request.body()

    async with httpx.AsyncClient() as http_client:
        resp = await http_client.request(
            method=request.method,
            url=downstream_url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            content=body,
        )

    return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
