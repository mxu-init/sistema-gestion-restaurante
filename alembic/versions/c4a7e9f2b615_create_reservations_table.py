"""create reservations table

Revision ID: c4a7e9f2b615
Revises: 71ad42bf89a7
Create Date: 2026-11-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4a7e9f2b615'
down_revision: Union[str, Sequence[str], None] = '71ad42bf89a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('num_people', sa.Integer(), nullable=False),
        sa.Column('reservation_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('table_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='confirmed', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.CheckConstraint('created_by > 0', name='ck_reservations_created_by'),
        sa.CheckConstraint('num_people > 0', name='ck_reservations_num_people'),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'seated', 'cancelled', 'no_show')",
            name='ck_reservations_status',
        ),
        sa.ForeignKeyConstraint(['table_id'], ['tables.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reservations_id'), 'reservations', ['id'], unique=False)
    op.create_index(
        'ix_reservations_table_slot',
        'reservations',
        ['table_id', 'reservation_date', 'start_time'],
        unique=False,
    )
    op.create_index(
        'ix_reservations_phone_slot',
        'reservations',
        ['phone', 'reservation_date', 'start_time'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_reservations_phone_slot', table_name='reservations')
    op.drop_index('ix_reservations_table_slot', table_name='reservations')
    op.drop_index(op.f('ix_reservations_id'), table_name='reservations')
    op.drop_table('reservations')
