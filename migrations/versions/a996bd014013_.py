"""empty message

Revision ID: a996bd014013
Revises: b072b632a292
Create Date: 2025-03-30 10:37:49.993258

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "a996bd014013"
down_revision = "b072b632a292"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE public.event SET tags = REPLACE(tags, ' ', '');")


def downgrade():
    pass
