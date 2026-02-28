"""add mdib column to tracks

Revision ID: c59bd0ce0f3d
Revises: 
Create Date: 2026-02-27 16:55:07.581471

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c59bd0ce0f3d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("releases", sa.Column("mbid", sa.String(), nullable=True))


def downgrade():
    op.drop_column("releases", "mbid")
