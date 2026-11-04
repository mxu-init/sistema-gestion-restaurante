"""add source columns to dishes

Revision ID: f3a1c8d29b47
Revises: 966cd847de5e
Create Date: 2026-11-02 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a1c8d29b47'
down_revision: Union[str, Sequence[str], None] = '966cd847de5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
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


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_dishes_source_source_id', table_name='dishes')
    op.drop_column('dishes', 'source_id')
    op.drop_column('dishes', 'source')
