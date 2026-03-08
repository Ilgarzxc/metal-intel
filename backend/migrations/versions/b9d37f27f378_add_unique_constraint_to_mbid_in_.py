"""add unique constraint to mbid in releases

Revision ID: b9d37f27f378
Revises: 1fb93d989f44
Create Date: 2026-03-08 17:57:02.354811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9d37f27f378'
down_revision: Union[str, Sequence[str], None] = '1fb93d989f44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Добавляем уникальное ограничение на mbid
    op.create_unique_constraint(
        "uq_releases_mbid",  # имя уникального ограничения
        "releases",          # таблица
        ["mbid"]             # колонка
    )


def downgrade():
    # Убираем уникальное ограничение при откате
    op.drop_constraint(
        "uq_releases_mbid",
        "releases",
        type_="unique"
    )