"""create tables

Revision ID: 8c938a804c11
Revises: 76ea12b38f94
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c938a804c11'
down_revision: Union[str, Sequence[str], None] = '76ea12b38f94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('tables',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('location', sa.String(length=20), nullable=False),
    sa.Column('capacity', sa.Integer(), nullable=False),
    sa.Column('max_capacity', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.CheckConstraint('capacity > 0', name='ck_tables_capacity'),
    sa.CheckConstraint("location IN ('indoor', 'outdoor')", name='ck_tables_location'),
    sa.CheckConstraint('max_capacity >= capacity', name='ck_tables_max_capacity'),
    sa.CheckConstraint('number > 0', name='ck_tables_number_positive'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tables_id'), 'tables', ['id'], unique=False)
    op.create_index(op.f('ix_tables_number'), 'tables', ['number'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tables_number'), table_name='tables')
    op.drop_index(op.f('ix_tables_id'), table_name='tables')
    op.drop_table('tables')
