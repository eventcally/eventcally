"""empty message

Revision ID: 84d692aa450c
Revises: 1615a65076d4
Create Date: 2025-05-06 15:22:30.775106

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "84d692aa450c"
down_revision = "1615a65076d4"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "apikey",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("admin_unit_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "(admin_unit_id IS NULL) <> (user_id IS NULL)",
            name=op.f("ck_apikey_apikey_admin_unit_xor_user"),
        ),
        sa.ForeignKeyConstraint(
            ["admin_unit_id"],
            ["adminunit.id"],
            name=op.f("fk_apikey_admin_unit_id_adminunit"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["user.id"],
            name=op.f("fk_apikey_created_by_id_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"],
            ["user.id"],
            name=op.f("fk_apikey_updated_by_id_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_apikey_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_apikey")),
        sa.UniqueConstraint("key_hash", name=op.f("uq_apikey_key_hash")),
        sa.UniqueConstraint(
            "name", "admin_unit_id", name="uq_apikey_name_admin_unit_id"
        ),
        sa.UniqueConstraint("name", "user_id", name="uq_apikey_name_user_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("apikey")
    # ### end Alembic commands ###
