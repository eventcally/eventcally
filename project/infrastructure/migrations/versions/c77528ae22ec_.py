"""Drop the retired User Favorites feature table

Revision ID: c77528ae22ec
Revises: 92dd815d2870
Create Date: 2026-09-19 17:05:00.000000

Written by hand for the same reason as 92dd815d2870: `include_name` in
migrations/env.py restricts reflection to tables present in the model metadata,
so once UserFavoriteEvents was removed from the models, autogenerate could no
longer see the table and reported "No changes in schema detected". The
downgrade mirrors the table as it existed at revision 92dd815d2870 (see
40873357f372 for the original create, and 6f7e83acf944 / cbac4166f9c0 for the
named constraints and ON DELETE CASCADE that create predates).

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c77528ae22ec"
down_revision = "92dd815d2870"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("user_favoriteevents")


def downgrade():
    op.create_table(
        "user_favoriteevents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
            name=op.f("fk_user_favoriteevents_event_id_event"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_user_favoriteevents_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_favoriteevents")),
        sa.UniqueConstraint(
            "user_id", "event_id", name=op.f("uq_user_favoriteevents_user_id")
        ),
    )
