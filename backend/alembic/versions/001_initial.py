"""initial

Revision ID: 001
Revises:
Create Date: 2026-06-07

"""
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # password service owns no tables — users table belongs to small-cmr-base
    pass


def downgrade() -> None:
    pass
