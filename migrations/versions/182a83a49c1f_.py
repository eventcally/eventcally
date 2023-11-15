"""empty message

Revision ID: 182a83a49c1f
Revises: c20d6d7575be
Create Date: 2023-11-13 15:50:05.343979

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "182a83a49c1f"
down_revision = "c20d6d7575be"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("locale", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("user", "locale")
