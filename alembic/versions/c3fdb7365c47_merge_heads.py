"""merge heads

Revision ID: c3fdb7365c47
Revises: 3190ffa0880e, 769f71322953
Create Date: 2026-11-11 10:04:59.835572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3fdb7365c47'
down_revision: Union[str, Sequence[str], None] = ('3190ffa0880e', '769f71322953')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
