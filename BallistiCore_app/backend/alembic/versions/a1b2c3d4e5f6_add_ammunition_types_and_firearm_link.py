"""add_ammunition_types_table_and_firearm_link

Revision ID: a1b2c3d4e5f6
Revises: e7efa56627a9
Create Date: 2026-06-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e7efa56627a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ammunition_types',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.add_column('firearms', sa.Column('ammunition_type_id', sa.String(length=36), nullable=True))
    op.create_foreign_key(
        'fk_firearms_ammunition_type_id',
        'firearms', 'ammunition_types',
        ['ammunition_type_id'], ['id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_firearms_ammunition_type_id', 'firearms', type_='foreignkey')
    op.drop_column('firearms', 'ammunition_type_id')
    op.drop_table('ammunition_types')
