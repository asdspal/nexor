"""Security utilities: JWT handling and SIWE verification.

Blueprint binding:
- Section 3.2, 7.1, 7.5: JWT HS256, 24h TTL, httpOnly cookie SameSite=Strict
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from eth_account import Account
from eth_account.messages import encode_defunct
from jose import JWTError, jwt

from app.core.config import ACCESS_TOKEN_EXPIRE, JWT_ALGORITHM, JWT_SECRET_KEY


class TokenError(Exception):
    """Raised when token validation fails."""


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or ACCESS_TOKEN_EXPIRE)
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:  # noqa: BLE001
        raise TokenError("Invalid or expired token") from exc


def verify_siwe_message(message: str, signature: str) -> str:
    """Verify SIWE (EIP-4361) signature and return recovered address (checksum).

    Uses eth-account to recover the address. Message is treated as an EIP-191
    personal_sign payload via encode_defunct, consistent with SIWE standard.
    """

    # Encode message for personal_sign style recovery
    encoded = encode_defunct(text=message)
    try:
        recovered = Account.recover_message(encoded, signature=signature)
    except Exception as exc:  # noqa: BLE001
        raise TokenError("Failed to verify SIWE signature") from exc

    return Account.to_checksum_address(recovered)

