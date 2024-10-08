"""empty message

Revision ID: 41512b20e07c
Revises: fd7794ece0b3
Create Date: 2020-07-17 19:54:25.703175

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "41512b20e07c"
down_revision = "fd7794ece0b3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TABLE event DROP CONSTRAINT IF EXISTS event_event_place_id_fkey;")
    # op.drop_constraint("event_event_place_id_fkey", "event", type_="foreignkey")
    op.create_foreign_key(None, "event", "eventplace", ["event_place_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "event", type_="foreignkey")
    op.create_foreign_key(
        "event_event_place_id_fkey", "event", "place", ["event_place_id"], ["id"]
    )
    # ### end Alembic commands ###
