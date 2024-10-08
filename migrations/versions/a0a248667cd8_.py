"""empty message

Revision ID: a0a248667cd8
Revises: e33f225323f3
Create Date: 2021-01-18 15:02:58.354511

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes
from project.models import EventAttendanceMode, EventTargetGroupOrigin

# revision identifiers, used by Alembic.
revision = "a0a248667cd8"
down_revision = "e33f225323f3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "eventsuggestion_eventcategories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_suggestion_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["eventcategory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["event_suggestion_id"],
            ["eventsuggestion.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "eventsuggestion", sa.Column("accessible_for_free", sa.Boolean(), nullable=True)
    )
    op.add_column("eventsuggestion", sa.Column("age_from", sa.Integer(), nullable=True))
    op.add_column("eventsuggestion", sa.Column("age_to", sa.Integer(), nullable=True))
    op.add_column(
        "eventsuggestion",
        sa.Column(
            "attendance_mode", dbtypes.IntegerEnum(EventAttendanceMode), nullable=True
        ),
    )
    op.add_column(
        "eventsuggestion", sa.Column("booked_up", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "eventsuggestion", sa.Column("end", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "eventsuggestion",
        sa.Column("expected_participants", sa.Integer(), nullable=True),
    )
    op.add_column(
        "eventsuggestion", sa.Column("kid_friendly", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "eventsuggestion", sa.Column("price_info", sa.UnicodeText(), nullable=True)
    )
    op.add_column(
        "eventsuggestion", sa.Column("recurrence_rule", sa.UnicodeText(), nullable=True)
    )
    op.add_column(
        "eventsuggestion",
        sa.Column("registration_required", sa.Boolean(), nullable=True),
    )
    op.add_column("eventsuggestion", sa.Column("tags", sa.UnicodeText(), nullable=True))
    op.add_column(
        "eventsuggestion",
        sa.Column(
            "target_group_origin",
            dbtypes.IntegerEnum(EventTargetGroupOrigin),
            nullable=True,
        ),
    )
    op.add_column(
        "eventsuggestion",
        sa.Column("ticket_link", sa.String(length=255), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("eventsuggestion", "ticket_link")
    op.drop_column("eventsuggestion", "target_group_origin")
    op.drop_column("eventsuggestion", "tags")
    op.drop_column("eventsuggestion", "registration_required")
    op.drop_column("eventsuggestion", "recurrence_rule")
    op.drop_column("eventsuggestion", "price_info")
    op.drop_column("eventsuggestion", "kid_friendly")
    op.drop_column("eventsuggestion", "expected_participants")
    op.drop_column("eventsuggestion", "end")
    op.drop_column("eventsuggestion", "booked_up")
    op.drop_column("eventsuggestion", "attendance_mode")
    op.drop_column("eventsuggestion", "age_to")
    op.drop_column("eventsuggestion", "age_from")
    op.drop_column("eventsuggestion", "accessible_for_free")
    op.drop_table("eventsuggestion_eventcategories")
    # ### end Alembic commands ###
