"""Async SQLAlchemy engine and session setup.

Constraints:
- Async SQLAlchemy 2.0.x
- Async driver: asyncpg
- Default URL per blueprint: postgresql+asyncpg://user:pass@localhost:5432/nexor
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/nexor"
)

Base = declarative_base()


def get_engine() -> AsyncEngine:
    return create_async_engine(DATABASE_URL, echo=False, future=True)


def get_sessionmaker(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    engine = engine or get_engine()
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async_session = get_sessionmaker()
    async with async_session() as session:
        yield session

