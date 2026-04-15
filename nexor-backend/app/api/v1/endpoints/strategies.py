"""Strategy listing endpoint with Redis cache (Blueprint Sections 3.3, 7.3).

Bindings:
- Table: strategies
- Endpoint: GET /api/strategies
- Cache: Redis 5 minutes (TTL=300s)
"""

from __future__ import annotations

import json
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.limiter import limiter
from app.core.redis import get_redis_client
from app.models.strategy import Strategy, StrategyCreditBand


router = APIRouter(prefix="/api/strategies", tags=["strategies"])

CACHE_TTL_SECONDS = 300


def _serialize_strategy(strategy: Strategy) -> dict[str, Any]:
    return {
        "id": str(strategy.id),
        "credit_band": strategy.credit_band,
        "title": strategy.title,
        "description": strategy.description,
        "steps": strategy.steps,
        "expected_apy": float(strategy.expected_apy),
        "risk_score": strategy.risk_score,
        "worst_case_scenario": strategy.worst_case_scenario,
        "protocols_used": strategy.protocols_used,
        "generated_at": strategy.generated_at.isoformat(),
        "expires_at": strategy.expires_at.isoformat(),
    }


@router.get("", summary="List strategies by credit band")
@limiter.exempt
async def list_strategies(
    band: str = Query(..., description="Credit band to filter strategies (A/B/C/D/NONE)"),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        band_enum = StrategyCreditBand(band)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid band")

    redis = get_redis_client()
    cache_key = f"strategy:{band_enum.value}"

    cached = await redis.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            # Fall through to refresh cache from DB
            pass

    result = await db.execute(
        select(Strategy)
        .where(Strategy.credit_band == band_enum)
        .order_by(Strategy.generated_at.desc())
    )
    strategies: List[Strategy] = result.scalars().all()

    serialized = [_serialize_strategy(strategy) for strategy in strategies]

    # If no strategies exist, return empty list (AI generation is optional and left to upstream flow)
    try:
        await redis.set(cache_key, json.dumps(serialized), ex=CACHE_TTL_SECONDS)
    except Exception:
        # Non-fatal cache failure
        pass

    return serialized
