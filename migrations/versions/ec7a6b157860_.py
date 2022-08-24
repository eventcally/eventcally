"""empty message

Revision ID: ec7a6b157860
Revises: 40873357f372
Create Date: 2022-08-23 15:09:34.578596

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "ec7a6b157860"
down_revision = "40873357f372"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "adminunit",
        sa.Column(
            "incoming_verification_requests_allowed",
            sa.Boolean(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "adminunit",
        sa.Column(
            "incoming_verification_requests_text", sa.UnicodeText(), nullable=True
        ),
    )


def downgrade():
    op.drop_column("adminunit", "incoming_verification_requests_text")
    op.drop_column("adminunit", "incoming_verification_requests_allowed")
