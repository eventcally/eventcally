"""empty message

Revision ID: d2c04be821a7
Revises: 6634c8f0b7fc
Create Date: 2023-09-07 22:20:57.918736

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "d2c04be821a7"
down_revision = "6634c8f0b7fc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "settings", sa.Column("announcement", sa.UnicodeText(), nullable=True)
    )


def downgrade():
    op.drop_column("settings", "announcement")
