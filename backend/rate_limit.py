from __future__ import annotations

import time
from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse

from .settings import settings


class TokenBucket:
    def __init__(self, rate_per_minute: int, burst: int) -> None:
        self.capacity = burst
        self.tokens = burst
        self.refill_rate_per_sec = rate_per_minute / 60.0
        self.last_refill = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.last_refill = now

        # refill tokens
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate_per_sec,
        )

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True

        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limit ultra simple par IP (token bucket en mémoire).

    - rate_per_minute: nombre de requêtes par minute
    - burst: capacité max de rafale
    """

    def __init__(
        self,
        app,
        rate_per_minute: int = settings.RATE_LIMIT_PER_MIN,
        burst: int = settings.RATE_LIMIT_BURST,
    ) -> None:
        super().__init__(app)
        self.rate_per_minute = rate_per_minute
        self.burst = burst
        self.buckets: Dict[str, TokenBucket] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        bucket = self.buckets.get(client_ip)
        if bucket is None:
            bucket = TokenBucket(self.rate_per_minute, self.burst)
            self.buckets[client_ip] = bucket

        if not bucket.allow():
            # Trop de requêtes
            return PlainTextResponse(
                "Trop de requêtes. Merci de réessayer dans quelques instants.",
                status_code=429,
            )

        response: Response = await call_next(request)
        return response
