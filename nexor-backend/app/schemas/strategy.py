"""Pydantic schemas for strategy generation (Blueprint Section 4.3 / 3.1).

Bindings:
- Schema mirrors strategies table columns for AI output validation
- Used by GPT-4o JSON mode response parsing
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from pydantic import BaseModel, Field, RootModel

from app.models.strategy import StrategyCreditBand


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class StrategyStep(BaseModel):
    title: str = Field(..., description="Step name")
    action: str = Field(..., description="What to do")
    rationale: str = Field(..., description="Why this step")
    protocol: str = Field(..., description="Protocol involved")


class StrategyGenerate(BaseModel):
    credit_band: StrategyCreditBand
    title: str
    description: str
    steps: List[StrategyStep]
    expected_apy: float
    risk_score: int = Field(..., ge=1, le=10)
    worst_case_scenario: str
    protocols_used: List[str]
    generated_at: datetime = Field(default_factory=_now_utc)
    expires_at: datetime = Field(default_factory=lambda: _now_utc() + timedelta(hours=24))


class StrategyGenerateRoot(RootModel[StrategyGenerate]):
    root: StrategyGenerate
