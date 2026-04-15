"""SQLAlchemy model for users table.

Blueprint binding (Extraction 2, Section 4.1):
- Columns: id, wallet_address, chain_id, credit_band, credit_proof_hash,
  credit_updated_at, sbt_token_id, created_at, updated_at
- Constraints: async SQLAlchemy 2.0.x, credit_band ENUM, wallet_address unique
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Enum, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CreditBand(enum.StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    wallet_address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    chain_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    credit_band: Mapped[CreditBand] = mapped_column(Enum(CreditBand, name="credit_band_enum"), nullable=False, default=CreditBand.D)
    credit_proof_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    credit_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sbt_token_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("wallet_address", name="uq_users_wallet_address"),
    )

