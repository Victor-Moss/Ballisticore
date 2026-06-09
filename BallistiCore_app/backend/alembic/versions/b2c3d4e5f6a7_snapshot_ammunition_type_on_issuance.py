"""snapshot_ammunition_type_on_issuance_records

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-07 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Snapshot of the firearm's ammunition type name at the moment of issue.
    # Stored as text (not an FK) so historical permits stay accurate even if the
    # ammunition type is later renamed or deactivated.
    op.add_column('permits', sa.Column('ammunition_type', sa.String(length=100), nullable=True))
    op.add_column('register', sa.Column('ammunition_type', sa.String(length=100), nullable=True))
    op.add_column('register_history', sa.Column('ammunition_type', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('register_history', 'ammunition_type')
    op.drop_column('register', 'ammunition_type')
    op.drop_column('permits', 'ammunition_type')
