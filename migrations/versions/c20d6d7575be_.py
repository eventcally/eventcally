"""empty message

Revision ID: c20d6d7575be
Revises: d2c04be821a7
Create Date: 2023-09-29 22:41:02.008405

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "c20d6d7575be"
down_revision = "d2c04be821a7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "adminunit",
        sa.Column(
            "incoming_verification_requests_postal_codes",
            postgresql.ARRAY(sa.Unicode(length=255)),
            server_default="{}",
            nullable=False,
        ),
    )
    op.create_index(
        "idx_adminunit_incoming_verification_requests_postal_codes",
        "adminunit",
        ["incoming_verification_requests_postal_codes"],
        unique=False,
        postgresql_using="gin",
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "idx_adminunit_incoming_verification_requests_postal_codes",
        table_name="adminunit",
        postgresql_using="gin",
    )
    op.drop_column("adminunit", "incoming_verification_requests_postal_codes")
    # ### end Alembic commands ###
