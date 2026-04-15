"""SQLAlchemy model for pool_snapshots table (Extraction 4.6)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PoolSnapshot(Base):
    __tablename__ = "pool_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocol_name: Mapped[str] = mapped_column(String(80), nullable=False)
    pool_address: Mapped[str] = mapped_column(String(42), nullable=False)
    apy_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    tvl_usd: Mapped[float] = mapped_column(Numeric(24, 2), nullable=False)
    utilization_pct: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_pool_snapshots_protocol_name", "protocol_name"),
        Index("ix_pool_snapshots_pool_address", "pool_address"),
        Index("ix_pool_snapshots_snapshot_at", "snapshot_at"),
    )
