"""init users

Revision ID: 49eba4502154
Revises: 
Create Date: 2026-04-14 21:56:27.635695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49eba4502154'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    credit_band_enum = sa.Enum(
        "A", "B", "C", "D", name="credit_band_enum"
    )
    credit_band_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("wallet_address", sa.String(length=255), nullable=False),
        sa.Column("chain_id", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("credit_band", credit_band_enum, nullable=False, server_default="D"),
        sa.Column("credit_proof_hash", sa.String(length=255), nullable=True),
        sa.Column("credit_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sbt_token_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("wallet_address", name="uq_users_wallet_address"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("users")
    sa.Enum(name="credit_band_enum").drop(op.get_bind(), checkfirst=True)
