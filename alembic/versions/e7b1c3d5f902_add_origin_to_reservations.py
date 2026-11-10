"""add origin to reservations

Revision ID: e7b1c3d5f902
Revises: c4a7e9f2b615
Create Date: 2026-11-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7b1c3d5f902'
down_revision: Union[str, Sequence[str], None] = 'c4a7e9f2b615'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'reservations',
        sa.Column('origin', sa.String(length=20), server_default='phone', nullable=False),
    )
    op.create_check_constraint(
        'ck_reservations_origin',
        'reservations',
        "origin IN ('phone', 'in_person')",
    )
    op.alter_column('reservations', 'origin', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_reservations_origin', 'reservations', type_='check')
    op.drop_column('reservations', 'origin')
