"""vault tables (passwords + shares)

Revision ID: 002
Revises: 001
Create Date: 2026-06-07
"""
import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "passwords",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("account_username", sa.String(255), nullable=False, index=True),
        sa.Column("encrypted_password", sa.Text, nullable=False),
        sa.Column("service", sa.String(255), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("owner_id", sa.Integer,
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.func.now()),
    )

    op.create_table(
        "password_shares",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("password_id", sa.Integer,
                  sa.ForeignKey("passwords.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("recipient_id", sa.Integer,
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("shared_by_id", sa.Integer,
                  sa.ForeignKey("users.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("permission", sa.Enum("read", "write", name="sharepermission"),
                  nullable=False, server_default="read"),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.func.now()),
        sa.UniqueConstraint("password_id", "recipient_id", name="uq_share_password_recipient"),
    )


def downgrade() -> None:
    op.drop_table("password_shares")
    op.drop_table("passwords")
