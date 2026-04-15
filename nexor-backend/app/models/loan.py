"""SQLAlchemy model for loans table (Extraction 4.4).

Note: users.id is INTEGER in current schema; user_id FK follows existing users table type.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Numeric, SmallInteger, String, UniqueConstraint, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class LoanStatus(enum.StrEnum):
    ACTIVE = "active"
    REPAID = "repaid"
    LIQUIDATED = "liquidated"


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    on_chain_loan_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    principal_usdc: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    collateral_token: Mapped[str] = mapped_column(String(42), nullable=False)
    collateral_amount: Mapped[float] = mapped_column(Numeric(36, 18), nullable=False)
    collateral_ratio_pct: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    interest_rate_bps: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus, name="loan_status_enum"), nullable=False, default=LoanStatus.ACTIVE
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    repaid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_repay_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    repayments = relationship("Repayment", back_populates="loan", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("on_chain_loan_id", name="uq_loans_on_chain_loan_id"),
        Index("ix_loans_user_id", "user_id"),
        Index("ix_loans_status", "status"),
    )
