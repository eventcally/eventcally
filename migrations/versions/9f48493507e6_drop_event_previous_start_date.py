"""Drop event.previous_start_date

Revision ID: 9f48493507e6
Revises: c77528ae22ec
Create Date: 2026-10-10 17:04:05.152534

The field is retired across the whole Event stack; there are no rolling
deploys, so stored values are discarded now. Downgrade restores an empty
column (original definition from ed6bb2084bbd_.py).

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f48493507e6"
down_revision = "c77528ae22ec"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("event", "previous_start_date")


def downgrade():
    op.add_column(
        "event",
        sa.Column("previous_start_date", sa.DateTime(timezone=True), nullable=True),
    )
