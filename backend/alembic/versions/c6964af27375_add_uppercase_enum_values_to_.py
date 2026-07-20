"""add_uppercase_enum_values_to_sessionstatus

Revision ID: c6964af27375
Revises: 0857b1fdd394
Create Date: 2026-07-20 23:03:27.384093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6964af27375'
down_revision: Union[str, None] = '0857b1fdd394'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'CREATED'")
        op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'READY'")
        op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")


def downgrade() -> None:
    pass
