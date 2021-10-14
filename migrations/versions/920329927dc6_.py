"""empty message

Revision ID: 920329927dc6
Revises: fca98f434287
Create Date: 2021-10-03 22:32:34.070105

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "920329927dc6"
down_revision = "fca98f434287"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "adminunitinvitation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_unit_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("admin_unit_name", sa.String(length=255), nullable=True),
        sa.Column(
            "relation_auto_verify_event_reference_requests",
            sa.Boolean(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("relation_verify", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["admin_unit_id"],
            ["adminunit.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "adminunit",
        sa.Column("can_invite_other", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "adminunitrelation",
        sa.Column("invited", sa.Boolean(), server_default="0", nullable=False),
    )


def downgrade():
    op.drop_column("adminunit", "can_invite_other")
    op.drop_column("adminunitrelation", "invited")
    op.drop_table("adminunitinvitation")
