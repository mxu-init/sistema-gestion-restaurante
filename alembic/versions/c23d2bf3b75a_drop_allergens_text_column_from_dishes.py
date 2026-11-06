"""drop allergens text column from dishes

Revision ID: c23d2bf3b75a
Revises: 76ea12b38f94
Create Date: 2026-11-06 10:48:22.233749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c23d2bf3b75a'
down_revision: Union[str, Sequence[str], None] = '76ea12b38f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('dishes', 'allergens')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('dishes', sa.Column('allergens', sa.String(), nullable=True))
