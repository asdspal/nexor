"""Loan management endpoints (Blueprint Section 7.4).

Endpoints:
- GET /api/loans: list user's loans joined with repayments
- POST /api/loans/simulate: compute collateral requirements and health factor
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.auth import get_current_user
from app.core.db import get_db_session
from app.models.loan import Loan
from app.models.repayment import Repayment
from app.models.user import CreditBand, User


router = APIRouter(prefix="/api/loans", tags=["loans"])


BAND_COLLATERAL_RATIO = {
    CreditBand.A: 1.20,  # 120%
    CreditBand.B: 1.30,  # 130%
    CreditBand.C: 1.40,  # 140%
    CreditBand.D: 1.50,  # 150%
}


def _serialize_repayment(repayment: Repayment) -> dict[str, Any]:
    return {
        "id": str(repayment.id),
        "amount_usdc": float(repayment.amount_usdc),
        "source": repayment.source,
        "tx_hash": repayment.tx_hash,
        "executed_at": repayment.executed_at.isoformat(),
    }


def _serialize_loan(loan: Loan) -> dict[str, Any]:
    return {
        "id": str(loan.id),
        "on_chain_loan_id": loan.on_chain_loan_id,
        "principal_usdc": float(loan.principal_usdc),
        "collateral_token": loan.collateral_token,
        "collateral_amount": float(loan.collateral_amount),
        "collateral_ratio_pct": float(loan.collateral_ratio_pct),
        "interest_rate_bps": loan.interest_rate_bps,
        "status": loan.status,
        "opened_at": loan.opened_at.isoformat(),
        "repaid_at": loan.repaid_at.isoformat() if loan.repaid_at else None,
        "auto_repay_enabled": loan.auto_repay_enabled,
        "repayments": [_serialize_repayment(r) for r in loan.repayments],
    }


@router.get("", summary="List loans for current user")
async def list_loans(
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Loan)
        .options(selectinload(Loan.repayments))
        .where(Loan.user_id == user.id)
        .order_by(Loan.opened_at.desc())
    )
    loans = result.scalars().all()
    return [_serialize_loan(loan) for loan in loans]


@router.post("/simulate", summary="Simulate loan collateral and health factor")
async def simulate_loan(
    payload: dict[str, Any],
    user: User = Depends(get_current_user),
):
    amount = payload.get("amount")
    collateral_token = payload.get("collateral_token")
    provided_collateral = payload.get("collateral_amount")

    if amount is None or collateral_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="amount and collateral_token are required")

    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="amount must be numeric")

    if amount_val <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="amount must be positive")

    band = user.credit_band or CreditBand.D
    ratio = BAND_COLLATERAL_RATIO.get(band, BAND_COLLATERAL_RATIO[CreditBand.D])

    required_collateral = amount_val * ratio

    if provided_collateral is None:
        provided_collateral = required_collateral
    try:
        provided_collateral_val = float(provided_collateral)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="collateral_amount must be numeric")

    if provided_collateral_val < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="collateral_amount must be non-negative")

    # Health factor = provided / required; capped at 2 decimals for readability
    health_factor = provided_collateral_val / required_collateral if required_collateral > 0 else 0

    return {
        "band": band,
        "collateral_ratio": ratio,
        "required_collateral": required_collateral,
        "provided_collateral": provided_collateral_val,
        "collateral_token": collateral_token,
        "loan_amount": amount_val,
        "health_factor": health_factor,
    }

