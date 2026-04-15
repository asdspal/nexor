"""Health check endpoint.

Blueprint binding:
- Section 3.2: /api/health
- Section 7.5: CORS only allow frontend origin

Checks:
- Postgres connectivity via SELECT 1
- Redis connectivity via PING
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.redis import get_redis_client


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", summary="Health check")
async def health_check(
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    # DB check
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "db": "unavailable", "redis": "unknown"},
        ) from exc

    # Redis check
    redis = get_redis_client()
    try:
        pong = await redis.ping()
        if pong is not True:
            raise RuntimeError("Unexpected Redis response")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "db": "connected", "redis": "unavailable"},
        ) from exc

    return {"status": "ok", "db": "connected", "redis": "connected"}

