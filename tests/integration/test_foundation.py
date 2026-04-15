"""Integration test for foundation validation (Step M.0.5).

Validates:
- /api/health returns 200 OK
- Confirms Postgres and Redis connectivity flags
"""

from __future__ import annotations

import os

import pytest
import httpx


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@pytest.mark.asyncio
async def test_health_endpoint_ok():
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=5) as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("db") == "connected"
    assert data.get("redis") == "connected"

