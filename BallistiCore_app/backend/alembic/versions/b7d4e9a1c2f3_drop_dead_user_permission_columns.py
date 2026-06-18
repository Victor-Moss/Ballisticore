"""drop dead user permission columns

Removes the five user-permission flags that were never enforced anywhere in the
app (no frontend gate, no backend check) and have now been deleted from the
Add/Modify User UI:

  - perm_clear_logs        (no log-clearing feature ever existed)
  - perm_carbine / perm_handgun / perm_rifle / perm_shotgun
        (weapon-type clearance at issue time is enforced against the *guard's*
         permitted_<type> field, not these operator flags)

The columns hold no meaningful data, so dropping them is non-destructive in
practice. Downgrade re-creates them with a default of false.

Revision ID: b7d4e9a1c2f3
Revises: f1a2b3c4d5e6
Create Date: 2026-06-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d4e9a1c2f3'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DEAD_COLUMNS = (
    'perm_clear_logs',
    'perm_carbine',
    'perm_handgun',
    'perm_rifle',
    'perm_shotgun',
)


def upgrade() -> None:
    for col in _DEAD_COLUMNS:
        op.drop_column('users', col)


def downgrade() -> None:
    for col in _DEAD_COLUMNS:
        op.add_column('users', sa.Column(col, sa.Boolean(), nullable=False, server_default='false'))
