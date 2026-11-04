"""add course type to categories

Revision ID: a64654ec8db5
Revises: f3a1c8d29b47
Create Date: 2026-11-03 11:33:12.654964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a64654ec8db5'
down_revision: Union[str, Sequence[str], None] = 'f3a1c8d29b47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'dishes',
        sa.Column('course_type', sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('dishes', 'course_type')
