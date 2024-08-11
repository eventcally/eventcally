"""empty message

Revision ID: fca98f434287
Revises: 811e16ed3bf0
Create Date: 2021-09-25 16:56:21.499233

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "fca98f434287"
down_revision = "811e16ed3bf0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "adminunit",
        sa.Column("can_verify_other", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "adminunitrelation",
        sa.Column("verify", sa.Boolean(), server_default="0", nullable=False),
    )


def downgrade():
    op.drop_column("adminunitrelation", "verify")
    op.drop_column("adminunit", "can_verify_other")
