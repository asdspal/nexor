"""add strategies and loans

Revision ID: 2462a5e4ca5e
Revises: 49eba4502154
Create Date: 2026-04-15 12:51:52.851557

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '2462a5e4ca5e'
down_revision: Union[str, Sequence[str], None] = '49eba4502154'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Enums
    credit_band_strategy_enum = sa.Enum("A", "B", "C", "D", "NONE", name="credit_band_strategy_enum")
    credit_band_strategy_enum.create(op.get_bind(), checkfirst=True)

    loan_status_enum = sa.Enum("active", "repaid", "liquidated", name="loan_status_enum")
    loan_status_enum.create(op.get_bind(), checkfirst=True)

    repayment_source_enum = sa.Enum("yield", "manual", name="repayment_source_enum")
    repayment_source_enum.create(op.get_bind(), checkfirst=True)

    # strategies
    op.create_table(
        "strategies",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("credit_band", credit_band_strategy_enum, nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("steps", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("expected_apy", sa.Numeric(6, 2), nullable=False),
        sa.Column("risk_score", sa.SmallInteger(), nullable=False),
        sa.Column("worst_case_scenario", sa.Text(), nullable=False),
        sa.Column("protocols_used", sa.ARRAY(sa.Text()), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_ai_response", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.CheckConstraint("risk_score BETWEEN 1 AND 10", name="ck_strategies_risk_score_range"),
    )
    op.create_index("ix_strategies_credit_band", "strategies", ["credit_band"], unique=False)
    op.create_index("ix_strategies_expires_at", "strategies", ["expires_at"], unique=False)
    op.create_index("ix_strategies_generated_at", "strategies", ["generated_at"], unique=False)

    # loans
    op.create_table(
        "loans",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("on_chain_loan_id", sa.BigInteger(), nullable=False),
        sa.Column("principal_usdc", sa.Numeric(18, 6), nullable=False),
        sa.Column("collateral_token", sa.String(length=42), nullable=False),
        sa.Column("collateral_amount", sa.Numeric(36, 18), nullable=False),
        sa.Column("collateral_ratio_pct", sa.Numeric(6, 2), nullable=False),
        sa.Column("interest_rate_bps", sa.SmallInteger(), nullable=False),
        sa.Column("status", loan_status_enum, nullable=False, server_default="active"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("repaid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_repay_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("on_chain_loan_id", name="uq_loans_on_chain_loan_id"),
    )
    op.create_index("ix_loans_user_id", "loans", ["user_id"], unique=False)
    op.create_index("ix_loans_status", "loans", ["status"], unique=False)

    # pool_snapshots
    op.create_table(
        "pool_snapshots",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("protocol_name", sa.String(length=80), nullable=False),
        sa.Column("pool_address", sa.String(length=42), nullable=False),
        sa.Column("apy_bps", sa.Integer(), nullable=False),
        sa.Column("tvl_usd", sa.Numeric(24, 2), nullable=False),
        sa.Column("utilization_pct", sa.Numeric(6, 2), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_pool_snapshots_protocol_name", "pool_snapshots", ["protocol_name"], unique=False)
    op.create_index("ix_pool_snapshots_pool_address", "pool_snapshots", ["pool_address"], unique=False)
    op.create_index("ix_pool_snapshots_snapshot_at", "pool_snapshots", ["snapshot_at"], unique=False)

    # repayments
    op.create_table(
        "repayments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("loan_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("loans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_usdc", sa.Numeric(18, 6), nullable=False),
        sa.Column("source", repayment_source_enum, nullable=False),
        sa.Column("tx_hash", sa.String(length=66), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("repayments")

    op.drop_index("ix_pool_snapshots_snapshot_at", table_name="pool_snapshots")
    op.drop_index("ix_pool_snapshots_pool_address", table_name="pool_snapshots")
    op.drop_index("ix_pool_snapshots_protocol_name", table_name="pool_snapshots")
    op.drop_table("pool_snapshots")

    op.drop_index("ix_loans_status", table_name="loans")
    op.drop_index("ix_loans_user_id", table_name="loans")
    op.drop_table("loans")

    op.drop_index("ix_strategies_generated_at", table_name="strategies")
    op.drop_index("ix_strategies_expires_at", table_name="strategies")
    op.drop_index("ix_strategies_credit_band", table_name="strategies")
    op.drop_table("strategies")

    sa.Enum(name="repayment_source_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="loan_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="credit_band_strategy_enum").drop(op.get_bind(), checkfirst=True)
