"""empty message

Revision ID: 35a6577b6af8
Revises: a0a248667cd8
Create Date: 2021-01-25 10:37:41.116909

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "35a6577b6af8"
down_revision = "a0a248667cd8"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "eventreference_event_id_admin_unit_id",
        "eventreference",
        ["event_id", "admin_unit_id"],
    )
    op.create_unique_constraint(
        "eventreferencerequest_event_id_admin_unit_id",
        "eventreferencerequest",
        ["event_id", "admin_unit_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "eventreferencerequest_event_id_admin_unit_id",
        "eventreferencerequest",
        type_="unique",
    )
    op.drop_constraint(
        "eventreference_event_id_admin_unit_id", "eventreference", type_="unique"
    )
    # ### end Alembic commands ###
