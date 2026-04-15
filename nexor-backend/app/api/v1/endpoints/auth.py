"""Authentication endpoints (SIWE + JWT).

Blueprint binding:
- Endpoints: POST /api/auth/siwe, POST /api/auth/refresh (Section 7.1)
- Security: JWT HS256, 24h TTL, httpOnly cookie, SameSite=Strict (Section 3.2, 7.5)
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import (
    ACCESS_TOKEN_COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE,
    ACCESS_TOKEN_EXPIRE_SECONDS,
)
from app.core.db import get_db_session
from app.core.security import TokenError, create_access_token, decode_token, verify_siwe_message
from app.models.user import User


router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _issue_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="strict",
        secure=False,  # flip to True behind HTTPS/production
        path="/",
    )


@router.post("/siwe", summary="Sign-In With Ethereum")
async def siwe_login(
    payload: dict[str, Any],
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    message = payload.get("message")
    signature = payload.get("signature")
    if not message or not signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message and signature required")

    try:
        wallet_address = verify_siwe_message(message, signature)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    # Upsert user
    result = await db.execute(select(User).where(User.wallet_address == wallet_address))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(wallet_address=wallet_address, chain_id=0)
        db.add(user)
        await db.flush()  # to assign id

    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=str(user.id), expires_delta=ACCESS_TOKEN_EXPIRE)
    await _issue_cookie(response, token, ACCESS_TOKEN_EXPIRE_SECONDS)

    return {"access_token": token, "token_type": "bearer", "user_id": user.id, "wallet_address": user.wallet_address}


@router.post("/refresh", summary="Refresh JWT")
async def refresh_token(
    request: Request,
    response: Response,
):
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        if not subject:
            raise TokenError("Missing subject")
    except (TokenError, JWTError) as exc:  # JWTError for completeness
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    new_token = create_access_token(subject=subject, expires_delta=ACCESS_TOKEN_EXPIRE)
    await _issue_cookie(response, new_token, ACCESS_TOKEN_EXPIRE_SECONDS)

    return {"access_token": new_token, "token_type": "bearer"}


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        if not subject:
            raise TokenError("Missing subject")
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    result = await db.execute(select(User).where(User.id == int(subject)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

