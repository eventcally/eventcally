"""empty message

Revision ID: ed6bb2084bbd
Revises: f1bc3fa623c7
Create Date: 2020-07-08 08:53:44.373606

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ed6bb2084bbd"
down_revision = "f1bc3fa623c7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "event",
        sa.Column("previous_start_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "eventdate", sa.Column("end", sa.DateTime(timezone=True), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("eventdate", "end")
    op.drop_column("event", "previous_start_date")
    # ### end Alembic commands ###
