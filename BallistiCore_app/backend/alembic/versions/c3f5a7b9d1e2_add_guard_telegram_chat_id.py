"""add telegram_chat_id to guards

Revision ID: c3f5a7b9d1e2
Revises: b7d4e9a1c2f3
Create Date: 2026-06-29 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f5a7b9d1e2'
down_revision: Union[str, None] = 'b7d4e9a1c2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('guards', sa.Column('telegram_chat_id', sa.String(length=40), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('guards', 'telegram_chat_id')
