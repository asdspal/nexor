"""Strategy Agent - Pool Indexer (Blueprint Section 3.1 / 4.6 / 9).

Behavior:
- Connect to HashKey Chain WebSocket RPC (public client analogue) using Web3.py.
- Poll known pools (placeholder addresses) for reserves/totalSupply.
- Compute TVL + mocked APY/utilization if formulas unavailable.
- Persist into pool_snapshots table via pool_service.save_pool_snapshot.

Notes:
- HashKey Chain pool ABIs are not provided; using UniswapV2-like ABI subset.
- WebSocket auto-reconnect with exponential backoff capped.
- Designed for Phase 2 local integration (python -m app.workers.indexer).
"""

from __future__ import annotations

import asyncio
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.providers.websocket import WebsocketProviderV2

from app.core.db import get_sessionmaker
from app.services.pool_service import save_pool_snapshot


# --- Config (env overrides allowed) -------------------------------------------------

HASHKEY_WS_RPC = os.getenv("HASHKEY_WS_RPC", "wss://example-hashkey.node/ws")

# Placeholder pools; replace with real HashKey DEX pools.
POOL_TARGETS = [
    {
        "protocol_name": "HashKeySwap",
        "pool_address": "0x0000000000000000000000000000000000000001",
        "token0_decimals": 18,
        "token1_decimals": 18,
        "price_token0_usd": Decimal("1"),
        "price_token1_usd": Decimal("1"),
    },
    {
        "protocol_name": "HashKeySwap",
        "pool_address": "0x0000000000000000000000000000000000000002",
        "token0_decimals": 6,
        "token1_decimals": 18,
        "price_token0_usd": Decimal("1"),
        "price_token1_usd": Decimal("2000"),
    },
]


# Minimal ABI subset for UniswapV2-like pools (reserves + totalSupply)
UNISWAP_V2_PAIR_ABI = json.loads(
    """
    [
      {"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},
      {"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}
    ]
    """
)


# --- Helpers -----------------------------------------------------------------------


def _init_web3(ws_url: str) -> Web3:
    provider = WebsocketProviderV2(ws_url, websocket_timeout=30)
    w3 = Web3(provider)
    # HashKey likely uses PoA-like chains; add middleware for safety.
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


def _calc_tvl_usd(
    reserve0: int,
    reserve1: int,
    token0_decimals: int,
    token1_decimals: int,
    price0_usd: Decimal,
    price1_usd: Decimal,
) -> Decimal:
    adj0 = Decimal(reserve0) / Decimal(10**token0_decimals)
    adj1 = Decimal(reserve1) / Decimal(10**token1_decimals)
    return adj0 * price0_usd + adj1 * price1_usd


def _mock_apy_bps(tvl_usd: Decimal) -> int:
    # Simple heuristic: higher TVL -> slightly lower APY; clamp to [50 bps, 1500 bps].
    apy = max(50, min(1500, int(1500 * math.exp(-float(tvl_usd) / 1_000_000) + 50)))
    return apy


def _mock_utilization_pct() -> Decimal:
    # Placeholder utilization: 60-85% randomish deterministic per minute
    minute = int(datetime.now(timezone.utc).timestamp() // 60)
    pseudo = (minute % 25) + 60  # cycles through 60..84
    return Decimal(pseudo)


async def _with_db(fn: Callable[[AsyncSession], Awaitable[Any]]) -> Any:
    Session = get_sessionmaker()
    async with Session() as session:
        return await fn(session)


# --- Indexer Loop ------------------------------------------------------------------


@dataclass
class PoolTarget:
    protocol_name: str
    pool_address: str
    token0_decimals: int
    token1_decimals: int
    price_token0_usd: Decimal
    price_token1_usd: Decimal


async def process_pool(w3: Web3, target: PoolTarget) -> None:
    pair = w3.eth.contract(address=Web3.to_checksum_address(target.pool_address), abi=UNISWAP_V2_PAIR_ABI)
    reserves = pair.functions.getReserves().call()
    total_supply = pair.functions.totalSupply().call()

    reserve0, reserve1, _ = reserves
    tvl_usd = _calc_tvl_usd(
        reserve0,
        reserve1,
        target.token0_decimals,
        target.token1_decimals,
        target.price_token0_usd,
        target.price_token1_usd,
    )

    apy_bps = _mock_apy_bps(tvl_usd)
    utilization = _mock_utilization_pct()

    async def _persist(db: AsyncSession):
        await save_pool_snapshot(
            db,
            protocol_name=target.protocol_name,
            pool_address=target.pool_address,
            apy_bps=apy_bps,
            tvl_usd=tvl_usd,
            utilization_pct=utilization,
            snapshot_at=datetime.now(timezone.utc),
        )
        await db.commit()

    await _with_db(_persist)


async def run_indexer(interval_seconds: int = 60) -> None:
    backoff = 1
    targets = [PoolTarget(**t) for t in POOL_TARGETS]

    while True:
        try:
            w3 = _init_web3(HASHKEY_WS_RPC)
            # Quick connectivity check
            _ = w3.eth.block_number
            backoff = 1  # reset on success

            while True:
                for target in targets:
                    try:
                        await process_pool(w3, target)
                    except Exception as exc:  # broad log; continue other pools
                        print(f"[pool-indexer] error processing {target.pool_address}: {exc}")
                await asyncio.sleep(interval_seconds)

        except Exception as exc:
            print(f"[pool-indexer] connection error: {exc}; reconnecting in {backoff}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


def main() -> None:
    asyncio.run(run_indexer())


if __name__ == "__main__":
    main()

