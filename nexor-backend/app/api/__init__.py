"""API package."""

from app.api.health import router as health_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.credit import router as credit_router
from app.api.v1.endpoints.strategies import router as strategies_router
from app.api.v1.endpoints.repayment import router as repayment_router
from app.api.v1.endpoints.loans import router as loans_router

__all__ = [
    "health_router",
    "auth_router",
    "credit_router",
    "strategies_router",
    "repayment_router",
    "loans_router",
]
