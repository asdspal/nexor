"""add credit_proofs table

Revision ID: 7b2b4d28b8e7
Revises: 2462a5e4ca5e
Create Date: 2026-04-15 09:11:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7b2b4d28b8e7"
down_revision = "2462a5e4ca5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "credit_proofs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("proof", sa.JSON(), nullable=False),
        sa.Column("public_signals", sa.JSON(), nullable=False),
        sa.Column("proof_hash", sa.String(length=255), nullable=False),
        sa.Column("tx_hash", sa.String(length=255), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_credit_proofs_user_id", "credit_proofs", ["user_id"], unique=False)
    op.create_index("ix_credit_proofs_proof_hash", "credit_proofs", ["proof_hash"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_credit_proofs_proof_hash", table_name="credit_proofs")
    op.drop_index("ix_credit_proofs_user_id", table_name="credit_proofs")
    op.drop_table("credit_proofs")

