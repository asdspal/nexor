"""GPT-4o Strategy Generator service (Blueprint Sections 2.1, 3.1, 4.3).

Responsibilities:
- Build DeFi yield strategy prompt with pool_snapshots context
- Call OpenAI Chat Completions (gpt-4o-2024-08-06) in JSON mode
- Validate response against StrategyGenerate schema
- Persist to strategies table with raw_ai_response
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable, Sequence, Tuple

from openai import OpenAI
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategy import Strategy, StrategyCreditBand
from app.schemas.strategy import StrategyGenerate, StrategyGenerateRoot


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-2024-08-06"
DEFAULT_EXPIRY_HOURS = 24


class StrategyGenerationError(Exception):
    """Raised when AI generation fails or validation fails."""


def _coerce_credit_band(band: StrategyCreditBand | str) -> StrategyCreditBand:
    return band if isinstance(band, StrategyCreditBand) else StrategyCreditBand(band)


def _build_prompt(credit_band: StrategyCreditBand, pool_data: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    pool_lines = []
    for idx, pool in enumerate(pool_data, start=1):
        pool_lines.append(
            f"{idx}. protocol={pool.get('protocol_name')} address={pool.get('pool_address')} "
            f"apy_bps={pool.get('apy_bps')} tvl_usd={pool.get('tvl_usd')} utilization_pct={pool.get('utilization_pct')}"
        )

    system_prompt = (
        "You are a DeFi yield optimizer. Generate a yield strategy."
        " Follow risk-aware best practices and produce valid JSON only."
    )

    user_prompt = (
        f"Credit band: {credit_band}.\n"
        "Use these pools as candidates (can select multiple):\n"
        + ("\n".join(pool_lines) if pool_lines else "(no pools provided, propose conservative idle/low-risk plan)")
        + "\nReturn fields: credit_band, title, description, steps[], expected_apy, risk_score, worst_case_scenario, protocols_used, generated_at (UTC ISO), expires_at (UTC ISO)."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise StrategyGenerationError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=OPENAI_API_KEY)


def _as_decimal(value: Decimal | float | int, quantize: str = "0.01") -> Decimal:
    dec = value if isinstance(value, Decimal) else Decimal(str(value))
    return dec.quantize(Decimal(quantize), rounding=ROUND_HALF_UP)


def _generate(
    *, credit_band: StrategyCreditBand | str, pool_data: Sequence[dict[str, Any]]
) -> Tuple[StrategyGenerate, dict[str, Any]]:
    """Shared generator that returns parsed model and raw response."""

    band = _coerce_credit_band(credit_band)
    client = _client()
    messages = _build_prompt(band, pool_data)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            response_format={"type": "json_object"},
            messages=messages,
            temperature=0.3,
        )
    except Exception as exc:  # noqa: BLE001
        raise StrategyGenerationError(f"OpenAI call failed: {exc}") from exc

    content = completion.choices[0].message.content
    try:
        parsed = StrategyGenerateRoot.model_validate_json(content).root
    except ValidationError as ve:
        raise StrategyGenerationError(f"Validation failed: {ve}") from ve

    return parsed, completion.model_dump()


def generate_strategy(credit_band: StrategyCreditBand | str, pool_data: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Synchronous helper for quick generation (no DB persistence)."""

    parsed, raw = _generate(credit_band=credit_band, pool_data=list(pool_data))
    return {"strategy": parsed.model_dump(), "raw_ai_response": raw}


async def generate_strategy_and_save(
    db: AsyncSession,
    *,
    credit_band: StrategyCreditBand | str,
    pool_data: Iterable[dict[str, Any]],
) -> Strategy:
    """Generate a strategy via GPT-4o, validate, and persist.

    Args:
        db: Async SQLAlchemy session
        credit_band: strategy credit band
        pool_data: iterable of pool snapshot dicts
    Returns:
        Persisted Strategy instance (uncommitted)
    Raises:
        StrategyGenerationError on failure
    """

    parsed, raw_ai_response = _generate(credit_band=credit_band, pool_data=list(pool_data))

    generated_at = parsed.generated_at or datetime.now(timezone.utc)
    expires_at = parsed.expires_at or generated_at + timedelta(hours=DEFAULT_EXPIRY_HOURS)

    strategy = Strategy(
        credit_band=parsed.credit_band,
        title=parsed.title,
        description=parsed.description,
        steps=[step.model_dump() for step in parsed.steps],
        expected_apy=_as_decimal(parsed.expected_apy),
        risk_score=parsed.risk_score,
        worst_case_scenario=parsed.worst_case_scenario,
        protocols_used=parsed.protocols_used,
        generated_at=generated_at,
        expires_at=expires_at,
        raw_ai_response=raw_ai_response,
    )

    db.add(strategy)
    await db.flush()
    return strategy
