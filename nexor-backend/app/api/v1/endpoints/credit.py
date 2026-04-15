"""Credit proof submission and status endpoints (Section 7.2).

Endpoints:
- POST /api/credit/submit: verify ZK proof via snarkjs, mint SBT (stub), persist credit_proofs, update user band
- GET /api/credit/status: return current user credit band and last proof hash

Rate limiting: 3 req/hour/IP via slowapi (Section 7.5)
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.core.db import get_db_session
from app.core.limiter import limiter
from app.models.credit_proof import CreditProof
from app.models.user import CreditBand, User
from app.services.verifier import VerificationError, mint_credit_band_stub, verify_proof_with_snarkjs


router = APIRouter(prefix="/api/credit", tags=["credit"])


@router.post("/submit", summary="Submit credit proof")
@limiter.limit("3/hour", key_func=get_remote_address)
async def submit_credit_proof(
    payload: dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    proof = payload.get("proof")
    public_signals = payload.get("publicSignals")
    band = payload.get("band")  # expected credit band string
    if not proof or not public_signals or not band:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="proof, publicSignals, band are required")

    if band not in CreditBand.__members__:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid band")

    repo_root = Path(__file__).resolve().parents[5]
    verification_key_path = repo_root / "nexor-circuits" / "verification_key.json"
    if not verification_key_path.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="verification key missing on server")

    try:
        is_valid = verify_proof_with_snarkjs(verification_key_path, proof, public_signals)
    except VerificationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid proof")

    # Stubbed on-chain mint
    tx_hash = mint_credit_band_stub(user.wallet_address, band)

    # Persist credit_proofs row
    proof_hash = hashlib.sha256(json.dumps(proof, sort_keys=True).encode()).hexdigest()
    credit_proof = CreditProof(
        user_id=user.id,
        proof=proof,
        public_signals=public_signals,
        proof_hash=proof_hash,
        tx_hash=tx_hash,
        is_valid=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(credit_proof)

    # Update user credit band & proof hash
    user.credit_band = CreditBand[band]
    user.credit_proof_hash = proof_hash
    user.credit_updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user)

    return {"status": "ok", "tx_hash": tx_hash, "band": user.credit_band, "proof_hash": proof_hash}


@router.get("/status", summary="Get current credit status")
async def credit_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    # fetch latest proof
    result = await db.execute(
        select(CreditProof)
        .where(CreditProof.user_id == user.id)
        .order_by(CreditProof.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    return {
        "band": user.credit_band,
        "proof_hash": user.credit_proof_hash,
        "latest_proof_id": str(latest.id) if latest else None,
        "tx_hash": latest.tx_hash if latest else None,
    }
