"""Drop the retired Event Lists feature tables

Revision ID: 92dd815d2870
Revises: 2fad15d1815e
Create Date: 2026-09-19 15:20:00.000000

Written by hand rather than via `flask db migrate`: `include_name` in
migrations/env.py restricts reflection to tables present in the model metadata,
so once EventList/EventEventLists were removed from the models, autogenerate
could no longer see the tables at all and reported "No changes in schema
detected". The downgrade mirrors the tables as they existed at revision
2fad15d1815e (see eba21922b9b7 for the original create, b13285e0d85f for the
app-installation tracking columns, and 74c5e8dae8ab / cceaf9b28134 /
58d8aae621e6 / cbac4166f9c0 for the named constraints).

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "92dd815d2870"
down_revision = "2fad15d1815e"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("event_eventlists")
    op.drop_table("eventlist")


def downgrade():
    op.create_table(
        "eventlist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Unicode(length=255), nullable=True),
        sa.Column("admin_unit_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_by_app_installation_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_app_installation_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["admin_unit_id"],
            ["adminunit.id"],
            name=op.f("fk_eventlist_admin_unit_id_adminunit"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_app_installation_id"],
            ["app_installation.id"],
            name=op.f("fk_eventlist_created_by_app_installation_id_app_installation"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["user.id"],
            name=op.f("fk_eventlist_created_by_id_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_app_installation_id"],
            ["app_installation.id"],
            name=op.f("fk_eventlist_updated_by_app_installation_id_app_installation"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"],
            ["user.id"],
            name=op.f("fk_eventlist_updated_by_id_user"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_eventlist")),
        sa.UniqueConstraint("name", "admin_unit_id", name=op.f("uq_eventlist_name")),
    )
    op.create_table(
        "event_eventlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("list_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
            name=op.f("fk_event_eventlists_event_id_event"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["list_id"],
            ["eventlist.id"],
            name=op.f("fk_event_eventlists_list_id_eventlist"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_eventlists")),
        sa.UniqueConstraint(
            "list_id", "event_id", name=op.f("uq_event_eventlists_list_id")
        ),
    )
