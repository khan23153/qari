"""Add Urdu translation audio URL to the ayahs table.

Revision ID: 0003
Revises: 0002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ayahs",
        sa.Column("audio_url_ur", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ayahs", "audio_url_ur")
