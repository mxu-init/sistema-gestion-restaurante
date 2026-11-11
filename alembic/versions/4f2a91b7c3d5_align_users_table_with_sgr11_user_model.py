"""align users table with sgr-11 user model

Adopts the richer user profile from branch sgr-11-user-model (name, created_at,
deleted_at, unique email index, password_hash) on top of the already-applied
create_users_table migration, avoiding a second create_table('users').

Revision ID: 4f2a91b7c3d5
Revises: c3fdb7365c47
Create Date: 2026-11-11 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f2a91b7c3d5'
down_revision: Union[str, Sequence[str], None] = 'c3fdb7365c47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # name: se agrega nullable y se rellena con el parte local del email
    op.add_column('users', sa.Column('name', sa.String(length=100), nullable=True))
    op.execute("UPDATE users SET name = split_part(email, '@', 1) WHERE name IS NULL")
    op.alter_column('users', 'name', existing_type=sa.String(length=100), nullable=False)

    # columna de credenciales: hashed_password -> password_hash (varchar 255)
    op.alter_column(
        'users',
        'hashed_password',
        new_column_name='password_hash',
        existing_type=sa.String(),
        type_=sa.String(length=255),
        existing_nullable=False,
    )

    # email: mas amplio, conserva el indice unico existente
    op.alter_column(
        'users',
        'email',
        existing_type=sa.String(length=100),
        type_=sa.String(length=255),
        existing_nullable=False,
    )

    # is_active: alinea el server default con el modelo
    op.alter_column(
        'users',
        'is_active',
        existing_type=sa.Boolean(),
        server_default='true',
        existing_nullable=False,
    )

    # auditoria
    op.add_column(
        'users',
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
    )
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'created_at')
    op.alter_column(
        'users',
        'is_active',
        existing_type=sa.Boolean(),
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        'users',
        'email',
        existing_type=sa.String(length=255),
        type_=sa.String(length=100),
        existing_nullable=False,
    )
    op.alter_column(
        'users',
        'password_hash',
        new_column_name='hashed_password',
        existing_type=sa.String(length=255),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.drop_column('users', 'name')
