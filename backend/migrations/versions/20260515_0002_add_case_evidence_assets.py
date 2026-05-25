"""add case evidence asset kinds

Revision ID: 20260515_0002
Revises: 20260419_0001
Create Date: 2026-05-15 00:00:00
"""

from alembic import op


revision = "20260515_0002"
down_revision = "20260419_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE asset_kind ADD VALUE IF NOT EXISTS 'VIOLATIONS_ANNOTATED'")
    op.execute("ALTER TYPE asset_kind ADD VALUE IF NOT EXISTS 'DRIVER_ZOOM'")


def downgrade():
    # PostgreSQL enum labels cannot be dropped safely without rebuilding the type.
    pass
