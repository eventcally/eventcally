"""empty message

Revision ID: 5fde26e1904d
Revises: 58d8aae621e6
Create Date: 2023-04-28 13:04:22.142011

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.elements import conv
from sqlalchemy.sql.naming import ConventionDict, _get_convention

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "5fde26e1904d"
down_revision = "58d8aae621e6"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    ctx = op.get_context()
    existing_metadata = sa.schema.MetaData()
    existing_metadata.reflect(bind=conn)
    target_metadata = ctx.opts["target_metadata"]

    for table_name, table in existing_metadata.tables.items():
        if table_name not in target_metadata.tables:
            continue

        for c in table.constraints:
            existing_name = c.name
            if not existing_name:
                continue

            convention = _get_convention(target_metadata.naming_convention, type(c))

            if not convention:
                continue

            target_c_name = conv(
                convention % ConventionDict(c, table, target_metadata.naming_convention)
            )
            if not target_c_name:
                continue

            if existing_name != target_c_name:
                op.execute(
                    f"ALTER TABLE public.{table_name} RENAME CONSTRAINT {existing_name} to {target_c_name};"
                )


def downgrade():
    pass
