"""SQLAlchemy model for credit_proofs table (Extraction 4.2).

Blueprint binding:
- Schema: credit_proofs (Section 4.2)
- Purpose: store submitted ZK proofs, verification status, and resulting tx hash
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CreditProof(Base):
    __tablename__ = "credit_proofs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    proof: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    public_signals: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    proof_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tx_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __mapper_args__ = {"eager_defaults": True}

