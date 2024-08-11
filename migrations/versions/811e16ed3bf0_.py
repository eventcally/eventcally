"""empty message

Revision ID: 811e16ed3bf0
Revises: 12ca023b94f8
Create Date: 2021-09-18 16:21:08.415884

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "811e16ed3bf0"
down_revision = "12ca023b94f8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_coorganizers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("organizer_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organizer_id"],
            ["eventorganizer.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "organizer_id"),
    )
    op.create_unique_constraint(
        "event_eventcategories_event_id_category_id",
        "event_eventcategories",
        ["event_id", "category_id"],
    )
    op.create_unique_constraint(
        "eventsuggestion_eventcategories_event_suggestion_id_category_id",
        "eventsuggestion_eventcategories",
        ["event_suggestion_id", "category_id"],
    )


def downgrade():
    op.drop_constraint(
        "eventsuggestion_eventcategories_event_suggestion_id_category_id",
        "eventsuggestion_eventcategories",
        type_="unique",
    )
    op.drop_constraint(
        "event_eventcategories_event_id_category_id",
        "event_eventcategories",
        type_="unique",
    )
    op.drop_table("event_coorganizers")
