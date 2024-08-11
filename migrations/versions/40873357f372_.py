"""empty message

Revision ID: 40873357f372
Revises: c5fbefbe9881
Create Date: 2022-01-13 23:08:14.098369

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "40873357f372"
down_revision = "c5fbefbe9881"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_favoriteevents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "event_id"),
    )


def downgrade():
    op.drop_table("user_favoriteevents")
