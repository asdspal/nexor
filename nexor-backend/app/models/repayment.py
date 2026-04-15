"""SQLAlchemy model for repayments table (Extraction 4.5).

Note: loans table is referenced by FK; ensure Loan model loads before metadata reflection.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class RepaymentSource(enum.StrEnum):
    YIELD = "yield"
    MANUAL = "manual"


class Repayment(Base):
    __tablename__ = "repayments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    amount_usdc: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[RepaymentSource] = mapped_column(Enum(RepaymentSource, name="repayment_source_enum"), nullable=False)
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    loan = relationship("Loan", back_populates="repayments")
