"""add_issuer_and_return_signatures

Dual e-signatures for issue and return:
  - issue:  guard ("Received by", existing) + issuing staff ("Issued by", new)
  - return: returning guard ("Returned by") + receiving staff ("Received by")

Revision ID: f1a2b3c4d5e6
Revises: b2c3d4e5f6a7
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    false = sa.text('false')

    # permits — issuer signature at issue + both return signatures
    op.add_column('permits', sa.Column('issuer_signed', sa.Boolean(), nullable=False, server_default=false))
    op.add_column('permits', sa.Column('issuer_signed_at', sa.DateTime(), nullable=True))
    op.add_column('permits', sa.Column('return_guard_signed', sa.Boolean(), nullable=False, server_default=false))
    op.add_column('permits', sa.Column('return_guard_signed_at', sa.DateTime(), nullable=True))
    op.add_column('permits', sa.Column('return_received_by', sa.String(length=36), nullable=True))
    op.add_column('permits', sa.Column('return_received_signed', sa.Boolean(), nullable=False, server_default=false))
    op.add_column('permits', sa.Column('return_received_signed_at', sa.DateTime(), nullable=True))
    op.create_foreign_key(
        'fk_permits_return_received_by_users', 'permits', 'users',
        ['return_received_by'], ['id'],
    )

    # register — issuing staff signature on the active issue
    op.add_column('register', sa.Column('issuer_signed', sa.Boolean(), nullable=False, server_default=false))
    op.add_column('register', sa.Column('issuer_signed_at', sa.DateTime(), nullable=True))

    # register_history — staff party signature for each ISSUED / RETURNED action
    op.add_column('register_history', sa.Column('issuer_signed', sa.Boolean(), nullable=False, server_default=false))
    op.add_column('register_history', sa.Column('issuer_signed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('register_history', 'issuer_signed_at')
    op.drop_column('register_history', 'issuer_signed')
    op.drop_column('register', 'issuer_signed_at')
    op.drop_column('register', 'issuer_signed')
    op.drop_constraint('fk_permits_return_received_by_users', 'permits', type_='foreignkey')
    op.drop_column('permits', 'return_received_signed_at')
    op.drop_column('permits', 'return_received_signed')
    op.drop_column('permits', 'return_received_by')
    op.drop_column('permits', 'return_guard_signed_at')
    op.drop_column('permits', 'return_guard_signed')
    op.drop_column('permits', 'issuer_signed_at')
    op.drop_column('permits', 'issuer_signed')
