"""Aggregate SQLAlchemy models for Alembic autogeneration."""

from app.models.user import User, CreditBand
from app.models.strategy import Strategy, StrategyCreditBand
from app.models.pool_snapshot import PoolSnapshot
from app.models.loan import Loan, LoanStatus
from app.models.repayment import Repayment, RepaymentSource
from app.models.credit_proof import CreditProof

__all__ = [
    "User",
    "CreditBand",
    "Strategy",
    "StrategyCreditBand",
    "PoolSnapshot",
    "Loan",
    "LoanStatus",
    "Repayment",
    "RepaymentSource",
    "CreditProof",
]
