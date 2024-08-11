"""empty message

Revision ID: 47c334ba5b86
Revises: 3f77c8693ae3
Create Date: 2023-03-26 23:03:44.678745

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "47c334ba5b86"
down_revision = "3f77c8693ae3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "newsletter_enabled", sa.Boolean(), server_default="1", nullable=False
        ),
    )


def downgrade():
    op.drop_column("user", "newsletter_enabled")
