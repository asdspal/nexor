"""Pool snapshot persistence helpers (Blueprint Section 4.6).

Bindings:
- Schema: pool_snapshots (Extraction 4.6)
- Layer: Strategy Agent storage helpers
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pool_snapshot import PoolSnapshot


def _as_decimal(value: Decimal | float | int, quantize: str = "0.01") -> Decimal:
    dec = value if isinstance(value, Decimal) else Decimal(str(value))
    return dec.quantize(Decimal(quantize), rounding=ROUND_HALF_UP)


async def save_pool_snapshot(
    db: AsyncSession,
    *,
    protocol_name: str,
    pool_address: str,
    apy_bps: int,
    tvl_usd: Decimal | float | int,
    utilization_pct: Decimal | float | int,
    snapshot_at: Optional[datetime] = None,
) -> PoolSnapshot:
    """Insert a pool_snapshots row.

    Args:
        db: Async SQLAlchemy session
        protocol_name: e.g., "HashKeySwap" / "UniswapV2"
        pool_address: on-chain pool address (42-char checksum preferred)
        apy_bps: APY in basis points (e.g., 500 == 5%)
        tvl_usd: total value locked in USD (Decimal-friendly)
        utilization_pct: utilization percentage (0-100)
        snapshot_at: optional snapshot timestamp (UTC)
    Returns:
        Persisted PoolSnapshot (uncommitted)
    """

    snapshot = PoolSnapshot(
        protocol_name=protocol_name,
        pool_address=pool_address,
        apy_bps=int(apy_bps),
        tvl_usd=_as_decimal(tvl_usd),
        utilization_pct=_as_decimal(utilization_pct),
        snapshot_at=snapshot_at or datetime.now(timezone.utc),
    )

    db.add(snapshot)
    await db.flush()
    return snapshot

