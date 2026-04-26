"""initial schema

Revision ID: 20260419_0001
Revises:
Create Date: 2026-04-19 18:30:00
"""

from alembic import op

from app.db.base import Base
import app.models  # noqa: F401

# revision identifiers, used by Alembic.
revision = "20260419_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
