"""empty message

Revision ID: 6893de0cb15b
Revises: 1fb9f679defb
Create Date: 2021-08-13 08:28:00.156404

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes
from project.models import PublicStatus

# revision identifiers, used by Alembic.
revision = "6893de0cb15b"
down_revision = "1fb9f679defb"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event",
        sa.Column(
            "public_status",
            dbtypes.IntegerEnum(PublicStatus),
            server_default=str(PublicStatus.published.value),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("event", "public_status")
