"""empty message

Revision ID: e759ca20884f
Revises: 4a5c083c649b
Create Date: 2021-09-08 14:38:28.975242

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "e759ca20884f"
down_revision = "4a5c083c649b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "adminunit",
        sa.Column("can_create_other", sa.Boolean(), server_default="0", nullable=False),
    )


def downgrade():
    op.drop_column("adminunit", "can_create_other")
