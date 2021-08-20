"""empty message

Revision ID: 924071080036
Revises: 6893de0cb15b
Create Date: 2021-08-20 08:15:53.480243

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "924071080036"
down_revision = "6893de0cb15b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "adminunit",
        sa.Column(
            "suggestions_enabled", sa.Boolean(), nullable=False, server_default="0"
        ),
    )


def downgrade():
    op.drop_column("adminunit", "suggestions_enabled")
