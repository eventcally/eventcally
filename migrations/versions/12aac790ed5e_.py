"""empty message

Revision ID: 12aac790ed5e
Revises: f350153a5691
Create Date: 2021-11-16 09:01:00.569170

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "12aac790ed5e"
down_revision = "f350153a5691"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "idx_event_fulltext",
        "event",
        [
            sa.text(
                """(
                (setweight(to_tsvector('german', coalesce(name, '')), 'A')) ||
                (setweight(to_tsvector('german', coalesce(tags, '')), 'B')) ||
                (setweight(to_tsvector('german', coalesce(description, '')), 'C'))
            )"""
            )
        ],
        postgresql_using="gin",
    )


def downgrade():
    op.drop_index("idx_event_fulltext")
