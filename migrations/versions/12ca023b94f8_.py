"""empty message

Revision ID: 12ca023b94f8
Revises: e759ca20884f
Create Date: 2021-09-09 13:13:24.802259

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "12ca023b94f8"
down_revision = "e759ca20884f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event", sa.Column("allday", sa.Boolean(), server_default="0", nullable=False)
    )
    op.add_column(
        "eventdate",
        sa.Column("allday", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "eventsuggestion",
        sa.Column("allday", sa.Boolean(), server_default="0", nullable=False),
    )


def downgrade():
    op.drop_column("eventsuggestion", "allday")
    op.drop_column("eventdate", "allday")
    op.drop_column("event", "allday")
