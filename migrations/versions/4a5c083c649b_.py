"""empty message

Revision ID: 4a5c083c649b
Revises: 924071080036
Create Date: 2021-08-30 15:10:07.807292

"""
import sqlalchemy as sa
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "4a5c083c649b"
down_revision = "924071080036"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "adminunitrelation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_admin_unit_id", sa.Integer(), nullable=False),
        sa.Column("target_admin_unit_id", sa.Integer(), nullable=False),
        sa.Column(
            "auto_verify_event_reference_requests",
            sa.Boolean(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "source_admin_unit_id != target_admin_unit_id", name="source_neq_target"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_admin_unit_id"], ["adminunit.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_admin_unit_id"], ["adminunit.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_admin_unit_id", "target_admin_unit_id"),
    )


def downgrade():
    op.drop_table("adminunitrelation")
