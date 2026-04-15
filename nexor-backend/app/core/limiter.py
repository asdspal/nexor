"""slowapi rate limiter configuration (Section 7.5).

- Default: 3 requests / hour per IP
- External: Redis (via slowapi default storage backed by in-memory unless configured)
"""

from __future__ import annotations

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.redis import REDIS_URL


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["3/hour"],
    storage_uri=REDIS_URL,
)

__all__ = ["limiter", "RateLimitExceeded", "_rate_limit_exceeded_handler"]
