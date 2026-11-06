"""seed base categories and allergens

Revision ID: aacc49216385
Revises: c23d2bf3b75a
Create Date: 2026-11-06 11:01:21.447978

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.reference_data import BASE_CATEGORIES, EU_ALLERGENS


# revision identifiers, used by Alembic.
revision: str = 'aacc49216385'
down_revision: Union[str, Sequence[str], None] = 'c23d2bf3b75a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    statements = [
        ("categories", name) for name in BASE_CATEGORIES
    ] + [
        ("allergens", name) for name in EU_ALLERGENS
    ]
    for table, name in statements:
        bind.execute(
            sa.text(
                f"INSERT INTO {table} (name) VALUES (:name) "
                "ON CONFLICT (name) DO NOTHING"
            ),
            {"name": name},
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Reference data may have existed before this migration ran, so it is not removed.
    pass
