"""empty message

Revision ID: becc71f97606
Revises: cceaf9b28134
Create Date: 2023-05-10 14:25:57.157442

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "becc71f97606"
down_revision = "cceaf9b28134"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("tos_accepted_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE public.user SET tos_accepted_at = CURRENT_TIMESTAMP;")


def downgrade():
    op.drop_column("user", "tos_accepted_at")
