"""Async Redis client factory.

Constraints:
- External service: Redis (blueprint Section 3.2, 7.5)
- Default URL: redis://localhost:6379/0
"""

from __future__ import annotations

import os

import redis.asyncio as redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


redis_client: redis.Redis = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


def get_redis_client() -> redis.Redis:
    """Return shared Redis async client."""

    return redis_client

