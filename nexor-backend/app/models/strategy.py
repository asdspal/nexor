"""SQLAlchemy model for strategies table (Extraction 4.3).

Blueprint bindings:
- Table: strategies (Section 4.3)
- Types: JSONB, TEXT[], NUMERIC(6,2)
- Constraints: credit_band ENUM includes NONE; protocols_used TEXT[]; steps JSONB
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, Numeric, SmallInteger, String, Text, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StrategyCreditBand(enum.StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    NONE = "NONE"


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_band: Mapped[StrategyCreditBand] = mapped_column(
        Enum(StrategyCreditBand, name="credit_band_strategy_enum"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    expected_apy: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    risk_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    worst_case_scenario: Mapped[str] = mapped_column(Text, nullable=False)
    protocols_used: Mapped[list[str]] = mapped_column(ARRAY(Text()), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_ai_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 1 AND 10", name="ck_strategies_risk_score_range"),
        Index("ix_strategies_credit_band", "credit_band"),
        Index("ix_strategies_expires_at", "expires_at"),
        Index("ix_strategies_generated_at", "generated_at"),
    )
