"""empty message

Revision ID: 30650020b4b7
Revises: 421660a4a792
Create Date: 2023-04-18 23:52:37.520530

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "30650020b4b7"
down_revision = "421660a4a792"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("current_login_at")
        batch_op.drop_column("current_login_ip")
        batch_op.drop_column("last_login_at")
        batch_op.drop_column("login_count")
        batch_op.drop_column("last_login_ip")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "last_login_ip",
                sa.VARCHAR(length=100),
                autoincrement=False,
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column("login_count", sa.INTEGER(), autoincrement=False, nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "last_login_at",
                postgresql.TIMESTAMP(),
                autoincrement=False,
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "current_login_ip",
                sa.VARCHAR(length=100),
                autoincrement=False,
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "current_login_at",
                postgresql.TIMESTAMP(),
                autoincrement=False,
                nullable=True,
            )
        )

    # ### end Alembic commands ###
