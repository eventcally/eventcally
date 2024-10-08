"""empty message

Revision ID: d952cd5df596
Revises: 5fde26e1904d
Create Date: 2023-05-01 17:27:48.768633

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "d952cd5df596"
down_revision = "5fde26e1904d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "fk_adminunitmember_user_id_user", "adminunitmember", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_adminunitmember_user_id_user"),
        "adminunitmember",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.add_column(
        "user", sa.Column("deletion_requested_at", sa.DateTime(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "deletion_requested_at")
    op.drop_constraint(
        op.f("fk_adminunitmember_user_id_user"), "adminunitmember", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_adminunitmember_user_id_user",
        "adminunitmember",
        "user",
        ["user_id"],
        ["id"],
    )
    # ### end Alembic commands ###
