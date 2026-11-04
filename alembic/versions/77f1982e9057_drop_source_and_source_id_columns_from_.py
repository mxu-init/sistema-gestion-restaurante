"""drop source and source_id columns from dishes

Revision ID: 77f1982e9057
Revises: 9cf838a2ce64
Create Date: 2026-11-03 14:23:13.000801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77f1982e9057'
down_revision: Union[str, Sequence[str], None] = '9cf838a2ce64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index('uq_dishes_source_source_id', table_name='dishes')
    op.drop_column('dishes', 'source_id')
    op.drop_column('dishes', 'source')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'dishes',
        sa.Column('source', sa.String(length=20), nullable=False, server_default='local'),
    )
    op.add_column('dishes', sa.Column('source_id', sa.String(length=50), nullable=True))
    op.create_index(
        'uq_dishes_source_source_id',
        'dishes',
        ['source', 'source_id'],
        unique=True,
        postgresql_where=sa.text('source_id IS NOT NULL AND deleted_at IS NULL'),
    )
