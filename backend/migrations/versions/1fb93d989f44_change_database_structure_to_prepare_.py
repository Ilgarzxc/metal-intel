"""change database structure to prepare for connection to external API

Revision ID: 1fb93d989f44
Revises: c59bd0ce0f3d
Create Date: 2026-02-28 15:55:26.817720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1fb93d989f44'
down_revision: Union[str, Sequence[str], None] = 'c59bd0ce0f3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create genres table
    op.create_table(
        "genres",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        )
    
    # Name indexing
    op.create_index("ix_genres_name", "genres", ["name"])

    # Create relation table and many-to-many connection
    op.create_table(
        "release_genres",
        sa.Column("release_id", sa.Integer, sa.ForeignKey("releases.id", ondelete="CASCADE"))
        sa.Column("genre_id", sa.Integer, sa.ForeignKey("genres.id", ondelete="CASCADE")),
    )
    # Delete old column: genres
    op.drop_column(
        "releases", "genre"
    )

def downgrade():
    op.add_column("releases", sa.Column("genre", sa.String(100), nullable=True))
    op.drop_table("release_genres")
    op.drop_index("ix_genres_name", table_name="genres")
    op.drop_table("genres")

