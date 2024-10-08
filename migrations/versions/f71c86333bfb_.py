"""empty message

Revision ID: f71c86333bfb
Revises: 4e913af88c33
Create Date: 2020-09-18 15:27:37.608869

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "f71c86333bfb"
down_revision = "4e913af88c33"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "analytics", sa.Column("value1", sa.Unicode(length=255), nullable=True)
    )
    op.add_column(
        "analytics", sa.Column("value2", sa.Unicode(length=255), nullable=True)
    )
    op.drop_column("analytics", "value")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "analytics", sa.Column("value", sa.TEXT(), autoincrement=False, nullable=True)
    )
    op.drop_column("analytics", "value2")
    op.drop_column("analytics", "value1")
    # ### end Alembic commands ###
