# Distributed Rate Limiter & API Gateway

A standalone gateway service that sits in front of any API and protects it with
per-user rate limiting, tiered access, and a circuit breaker for downstream
failures. Built to explore how production API infrastructure actually works,
not just how to use someone else's rate limiter.

## Why this exists

Every production API needs to answer two questions on every request:

1. **Is this specific user asking too much, too fast?** (rate limiting)
2. **Is the service we're about to call already failing, and should we even
   bother trying?** (circuit breaking)

Most developers have only ever *used* a rate limiter (Django REST throttling,
nginx limits, a cloud provider's built-in one). This project builds both
pieces from scratch to understand the actual trade-offs involved, using
Redis as shared state so the logic is correct even across multiple gateway
instances — not just within a single process.

## Architecture

```
Client → [Rate Limiter Gateway] → [Downstream API]
              ↓
          Redis (shared state: rate limits + circuit breaker)
```

Every request to `/proxy/{path}`:
1. Is authenticated via JWT (`Authorization: Bearer <token>`), which encodes
   the user's ID and tier (`free` / `pro` / `enterprise`)
2. Is checked against that tier's rate limit, using whichever algorithm is
   currently active
3. Is checked against the circuit breaker's state for the downstream service
4. If both checks pass, is forwarded to the real downstream API, and the
   response is relayed back to the caller

## Rate limiting algorithms

Three algorithms are implemented behind a common interface
(`RateLimiterStrategy`), switchable via one config value
(`ACTIVE_ALGORITHM` in `.env` / `docker-compose.yml`) with no other code
changes required — a strategy pattern, so the gateway itself never needs to
know which algorithm is active.

| Algorithm | Storage per user | Allows bursts? | Accuracy |
|---|---|---|---|
| **Fixed Window** | 1 counter | Yes, exploitable at window boundaries | Weakest |
| **Token Bucket** | 2 values (tokens, last refill) | Yes, intentionally, up to bucket size | Good |
| **Sliding Window Log** | 1 entry per request in the window | No | Best |

**Fixed Window** buckets time into fixed slots (`floor(now / window_seconds)`)
and counts requests per slot using Redis `INCR`/`EXPIRE`. Simplest and
cheapest, but a user can send `limit` requests at the very end of one window
and `limit` more at the start of the next, briefly doubling their effective
rate.

**Token Bucket** models a bucket that refills continuously at a fixed rate.
Rather than running a background job to add tokens, refill is computed
lazily on each request: `tokens_now = min(capacity, stored_tokens + elapsed *
refill_rate)`. This allows saved-up bursts without the boundary exploit
fixed window has — the same approach used by Stripe and AWS.

**Sliding Window Log** keeps an actual timestamp per request in a Redis
sorted set (`ZSET`), trims anything older than `now - window` on every
check, and counts what's left. This is the mathematically exact definition
of "rate limit," with no exploitable boundary — but memory cost scales
directly with request volume, since every request adds an entry until it
ages out.

### The hybrid not implemented here: Sliding Window Counter

At high scale, sliding window log's per-request storage becomes expensive.
A common production compromise (used by systems like Cloudflare's rate
limiter) keeps only two fixed-window counters — current and previous — and
blends them with a weighted average based on how far into the current
window you are:

```
estimated_count = (previous_window_count * overlap_fraction) + current_window_count
overlap_fraction = 1 - (time_elapsed_in_current_window / window_seconds)
```

This gets most of sliding window log's accuracy (no hard boundary to
exploit) at close to fixed window's storage cost (two integers instead of a
growing set). Not implemented here since three algorithms already
demonstrate the full trade-off space, but it's the answer to "how would you
make this cheaper at scale."

## Circuit breaker

Separately from rate limiting (which protects against *too many* requests),
the circuit breaker protects against calling a downstream service that's
*already broken* — failing fast instead of waiting out a timeout on every
request to a service known to be down.

Three states, stored per downstream target in Redis:

- **CLOSED** — normal operation, requests pass through; failures are counted
- **OPEN** — tripped after `failure_threshold` consecutive/recent failures;
  every request is rejected immediately (`503`) without attempting the call
- **HALF_OPEN** — after a `cooldown_seconds` wait, exactly one request is let
  through as a recovery probe. Success → back to CLOSED. Failure → back to
  OPEN for another cooldown.

## Tiered access

JWTs carry a `tier` claim (`free` / `pro` / `enterprise`), each mapped to
its own request limit in `app/config.py`. The same rate-limiting code path
handles all tiers — only the numbers differ.

## Project structure

```
app/
├── main.py              # FastAPI app, auth + rate limit + circuit breaker + proxy
├── auth.py               # JWT decoding, tier lookup
├── config.py              # settings, tier limits, active algorithm
├── redis_client.py        # shared Redis connection
├── circuit_breaker.py     # circuit breaker (Redis-backed state)
└── limiters/
    ├── base.py            # RateLimiterStrategy interface
    ├── fixed_window.py
    ├── token_bucket.py
    └── sliding_window.py
downstream/                # dummy API this gateway proxies to, for local testing
tests/
└── test_limiters.py
docker-compose.yml          # gateway + redis + downstream, wired together
```

## Running it

```
docker-compose up --build
```

This builds the gateway and downstream images, pulls Redis, and starts all
three on a shared internal network. Once running:

- `http://localhost:8000/docs` — Swagger UI for the gateway
- `http://localhost:8000/health` — confirms the service is up and which
  algorithm is active

Generate a test JWT to authenticate requests:

```python
import jwt, time
print(jwt.encode(
    {"sub": "test-user", "tier": "free", "exp": time.time() + 3600},
    "dev-secret-change-me", algorithm="HS256"))
```

Use it as `Authorization: Bearer <token>` when calling `/proxy/{path}`.

## Testing

```
pytest tests/ -v
```

Tests use `fakeredis` (an in-memory Redis stand-in) so they run without
Docker or a real Redis instance. Each algorithm is tested for:
- Allowing requests up to the limit, then blocking beyond it
- Isolating limits correctly per user
- Actually resetting/refilling once a real time window passes (not just
  within a single instant — this catches boundary and staleness bugs that
  same-instant tests would miss)

## Load testing

```
locust -f locustfile.py --host http://localhost:8000
```

Then open `http://localhost:8089` to configure concurrent users and watch
live requests/sec and latency.

<!-- TODO once run: paste your actual benchmark numbers here, e.g.
"Sustained ___ req/sec across ___ concurrent users with ___ms p95 latency
added by the rate-limit check." -->

## Known limitations

- `INCR` + `EXPIRE` in fixed window are two separate Redis calls, not
  wrapped in a transaction — a crash between them would leave a key without
  an expiry. Rare in practice; the fix would be a Redis `MULTI`/`EXEC`
  pipeline.
- The circuit breaker currently only treats connection-level failures
  (unreachable downstream) as failures — not downstream responses with
  `5xx` status codes. Extending `record_failure` to cover that is a
  straightforward next step.
