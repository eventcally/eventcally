"""empty message

Revision ID: ef547963d7f0
Revises: 182a83a49c1f
Create Date: 2023-11-25 10:12:48.763298

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "ef547963d7f0"
down_revision = "182a83a49c1f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "settings",
        sa.Column("planning_external_calendars", sa.UnicodeText(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("settings", "planning_external_calendars")
    # ### end Alembic commands ###
