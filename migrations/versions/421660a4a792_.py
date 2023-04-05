"""empty message

Revision ID: 421660a4a792
Revises: 47c334ba5b86
Create Date: 2023-04-05 18:09:03.913610

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "421660a4a792"
down_revision = "47c334ba5b86"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("created_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("user", "created_at")
