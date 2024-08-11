"""empty message

Revision ID: cce1284874fa
Revises: b128cc637447
Create Date: 2020-07-26 15:48:47.723256

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "cce1284874fa"
down_revision = "b128cc637447"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "adminunit", sa.Column("short_name", sa.Unicode(length=100), nullable=True)
    )
    op.add_column(
        "organization", sa.Column("short_name", sa.Unicode(length=100), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("organization", "short_name")
    op.drop_column("adminunit", "short_name")
    # ### end Alembic commands ###
