"""Repayment trigger endpoint (Internal) - Blueprint Section 7.4.

- POST /api/repayment/trigger (protected by X-Cron-Key)
- Logic: fetch active loans with auto_repay_enabled, call NexorLend.autoRepay, insert repayments row.
"""

from __future__ import annotations

import decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3
from web3.middleware import geth_poa_middleware

from app.core.config import CRON_INTERNAL_KEY, LEND_CONTRACT_ADDRESS, LEND_PRIVATE_KEY, LEND_RPC_URL, USDC_DECIMALS
from app.core.db import get_db_session
from app.core.limiter import limiter, RateLimitExceeded
from app.models.loan import Loan, LoanStatus
from app.models.repayment import Repayment, RepaymentSource


router = APIRouter(prefix="/api/repayment", tags=["repayment"], include_in_schema=False)


def _get_web3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(LEND_RPC_URL))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


def _get_lend_contract(w3: Web3):
    if not LEND_CONTRACT_ADDRESS:
        raise RuntimeError("LEND_CONTRACT_ADDRESS not configured")
    # Minimal ABI for autoRepay(uint256 loanId, uint256 amount)
    abi = [
        {
            "inputs": [
                {"internalType": "uint256", "name": "loanId", "type": "uint256"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"},
            ],
            "name": "autoRepay",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        }
    ]
    return w3.eth.contract(address=Web3.to_checksum_address(LEND_CONTRACT_ADDRESS), abi=abi)


async def _process_repayments(db: AsyncSession) -> dict[str, Any]:
    result = await db.execute(
        select(Loan).where(Loan.status == LoanStatus.ACTIVE, Loan.auto_repay_enabled == True)  # noqa: E712
    )
    loans = result.scalars().all()

    if not loans:
        return {"processed": 0}

    try:
        w3 = _get_web3()
        contract = _get_lend_contract(w3)
        account = w3.eth.account.from_key(LEND_PRIVATE_KEY) if LEND_PRIVATE_KEY else None
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    processed = 0
    tx_hashes: list[str] = []

    for loan in loans:
        # Placeholder: compute due as principal for now (improve with interest calc when available)
        principal = decimal.Decimal(str(loan.principal_usdc))
        amount_wei = int(principal * (10**USDC_DECIMALS))

        if account is None:
            # Offline stub call (no signing) for environments without key
            tx_hash_hex = f"stub-{loan.on_chain_loan_id}-{amount_wei}"
        else:
            try:
                tx = contract.functions.autoRepay(loan.on_chain_loan_id, amount_wei).build_transaction(
                    {
                        "from": account.address,
                        "nonce": w3.eth.get_transaction_count(account.address),
                        "gas": 400_000,
                        "gasPrice": w3.eth.gas_price,
                    }
                )
                signed = account.sign_transaction(tx)
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                tx_hash_hex = tx_hash.hex()
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        repayment = Repayment(
            loan_id=loan.id,
            amount_usdc=principal,
            source=RepaymentSource.YIELD,
            tx_hash=tx_hash_hex,
        )
        db.add(repayment)
        processed += 1
        tx_hashes.append(tx_hash_hex)

    await db.commit()
    return {"processed": processed, "tx_hashes": tx_hashes}


@router.post("/trigger", summary="Trigger auto repayment (internal)")
@limiter.exempt
async def trigger_repayment(
    x_cron_key: str = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db_session),
):
    if x_cron_key != CRON_INTERNAL_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid cron key")

    try:
        result = await _process_repayments(db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return result
