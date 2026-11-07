"""add terrace location

Revision ID: 71ad42bf89a7
Revises: 8c938a804c11
Create Date: 2026-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '71ad42bf89a7'
down_revision: Union[str, Sequence[str], None] = '8c938a804c11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('ck_tables_location', 'tables', type_='check')
    op.create_check_constraint(
        'ck_tables_location',
        'tables',
        "location IN ('indoor', 'outdoor', 'terrace')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_tables_location', 'tables', type_='check')
    op.create_check_constraint(
        'ck_tables_location',
        'tables',
        "location IN ('indoor', 'outdoor')",
    )
