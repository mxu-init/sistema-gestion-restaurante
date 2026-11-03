"""add allergens, drop course_type, fix is_available

Revision ID: 9cf838a2ce64
Revises: a64654ec8db5
Create Date: 2026-11-03 13:43:59.830383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9cf838a2ce64'
down_revision: Union[str, Sequence[str], None] = 'a64654ec8db5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('dishes', sa.Column('allergens', sa.String(), nullable=True))

    op.execute("UPDATE dishes SET is_available = true WHERE is_available IS NULL")
    op.alter_column(
        'dishes',
        'is_available',
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text('true'),
    )

    op.drop_column('dishes', 'course_type')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'dishes',
        sa.Column('course_type', sa.String(length=20), nullable=True),
    )
    op.alter_column(
        'dishes',
        'is_available',
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
    op.drop_column('dishes', 'allergens')
