"""Application configuration (secrets and security settings).

Blueprint binding:
- Section 3.2 / 7.5: JWT HS256, 24h TTL, httpOnly cookie SameSite=Strict
"""

from __future__ import annotations

import os
from datetime import timedelta


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-prod")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(hours=24)
ACCESS_TOKEN_EXPIRE_SECONDS = int(ACCESS_TOKEN_EXPIRE.total_seconds())
ACCESS_TOKEN_COOKIE_NAME = os.getenv("JWT_COOKIE_NAME", "access_token")

# --- Cron / repayment settings -------------------------------------------------------

CRON_INTERNAL_KEY = os.getenv("CRON_INTERNAL_KEY", "secret")
REPAY_CRON_URL = os.getenv("REPAY_CRON_URL", "http://localhost:8000/api/repayment/trigger")
REPAY_CRON_ENABLED = os.getenv("REPAY_CRON_ENABLED", "true").lower() == "true"

# --- NexorLend contract settings -----------------------------------------------------

LEND_RPC_URL = os.getenv("LEND_RPC_URL", os.getenv("HASHKEY_RPC_URL", "http://localhost:8545"))
LEND_CONTRACT_ADDRESS = os.getenv("LEND_CONTRACT_ADDRESS")
LEND_PRIVATE_KEY = os.getenv("LEND_PRIVATE_KEY")
USDC_DECIMALS = int(os.getenv("USDC_DECIMALS", "6"))
