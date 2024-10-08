"""empty message

Revision ID: cceaf9b28134
Revises: d952cd5df596
Create Date: 2023-05-01 18:02:53.515904

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "cceaf9b28134"
down_revision = "d952cd5df596"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "fk_adminunit_created_by_id_user", "adminunit", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_adminunit_updated_by_id_user", "adminunit", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_adminunit_updated_by_id_user"),
        "adminunit",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_adminunit_created_by_id_user"),
        "adminunit",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_adminunitinvitation_updated_by_id_user",
        "adminunitinvitation",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_adminunitinvitation_created_by_id_user",
        "adminunitinvitation",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_adminunitinvitation_updated_by_id_user"),
        "adminunitinvitation",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_adminunitinvitation_created_by_id_user"),
        "adminunitinvitation",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_adminunitrelation_updated_by_id_user",
        "adminunitrelation",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_adminunitrelation_created_by_id_user",
        "adminunitrelation",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_adminunitrelation_updated_by_id_user"),
        "adminunitrelation",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_adminunitrelation_created_by_id_user"),
        "adminunitrelation",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_customwidget_updated_by_id_user", "customwidget", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_customwidget_created_by_id_user", "customwidget", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_customwidget_updated_by_id_user"),
        "customwidget",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_customwidget_created_by_id_user"),
        "customwidget",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("fk_event_updated_by_id_user", "event", type_="foreignkey")
    op.drop_constraint("fk_event_created_by_id_user", "event", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_event_created_by_id_user"),
        "event",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_event_updated_by_id_user"),
        "event",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_eventlist_created_by_id_user", "eventlist", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_eventlist_updated_by_id_user", "eventlist", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_eventlist_updated_by_id_user"),
        "eventlist",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_eventlist_created_by_id_user"),
        "eventlist",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_eventorganizer_updated_by_id_user", "eventorganizer", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_eventorganizer_created_by_id_user", "eventorganizer", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_eventorganizer_updated_by_id_user"),
        "eventorganizer",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_eventorganizer_created_by_id_user"),
        "eventorganizer",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_eventplace_created_by_id_user", "eventplace", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_eventplace_updated_by_id_user", "eventplace", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_eventplace_created_by_id_user"),
        "eventplace",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_eventplace_updated_by_id_user"),
        "eventplace",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_eventreference_created_by_id_user", "eventreference", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_eventreference_updated_by_id_user", "eventreference", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_eventreference_updated_by_id_user"),
        "eventreference",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_eventreference_created_by_id_user"),
        "eventreference",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_eventreferencerequest_updated_by_id_user",
        "eventreferencerequest",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_eventreferencerequest_created_by_id_user",
        "eventreferencerequest",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_eventreferencerequest_created_by_id_user"),
        "eventreferencerequest",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_eventreferencerequest_updated_by_id_user"),
        "eventreferencerequest",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(
        "fk_eventsuggestion_created_by_id_user", "eventsuggestion", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_eventsuggestion_updated_by_id_user", "eventsuggestion", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_eventsuggestion_created_by_id_user"),
        "eventsuggestion",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_eventsuggestion_updated_by_id_user"),
        "eventsuggestion",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("fk_image_updated_by_id_user", "image", type_="foreignkey")
    op.drop_constraint("fk_image_created_by_id_user", "image", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_image_updated_by_id_user"),
        "image",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_image_created_by_id_user"),
        "image",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("fk_location_created_by_id_user", "location", type_="foreignkey")
    op.drop_constraint("fk_location_updated_by_id_user", "location", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_location_created_by_id_user"),
        "location",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_location_updated_by_id_user"),
        "location",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("fk_settings_updated_by_id_user", "settings", type_="foreignkey")
    op.drop_constraint("fk_settings_created_by_id_user", "settings", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_settings_created_by_id_user"),
        "settings",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_settings_updated_by_id_user"),
        "settings",
        "user",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        op.f("fk_settings_updated_by_id_user"), "settings", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_settings_created_by_id_user"), "settings", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_settings_created_by_id_user", "settings", "user", ["created_by_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_settings_updated_by_id_user", "settings", "user", ["updated_by_id"], ["id"]
    )
    op.drop_constraint(
        op.f("fk_location_updated_by_id_user"), "location", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_location_created_by_id_user"), "location", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_location_updated_by_id_user", "location", "user", ["updated_by_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_location_created_by_id_user", "location", "user", ["created_by_id"], ["id"]
    )
    op.drop_constraint(op.f("fk_image_created_by_id_user"), "image", type_="foreignkey")
    op.drop_constraint(op.f("fk_image_updated_by_id_user"), "image", type_="foreignkey")
    op.create_foreign_key(
        "fk_image_created_by_id_user", "image", "user", ["created_by_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_image_updated_by_id_user", "image", "user", ["updated_by_id"], ["id"]
    )
    op.drop_constraint(
        op.f("fk_eventsuggestion_updated_by_id_user"),
        "eventsuggestion",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_eventsuggestion_created_by_id_user"),
        "eventsuggestion",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_eventsuggestion_updated_by_id_user",
        "eventsuggestion",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_eventsuggestion_created_by_id_user",
        "eventsuggestion",
        "user",
        ["created_by_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_eventreferencerequest_updated_by_id_user"),
        "eventreferencerequest",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_eventreferencerequest_created_by_id_user"),
        "eventreferencerequest",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_eventreferencerequest_created_by_id_user",
        "eventreferencerequest",
        "user",
        ["created_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_eventreferencerequest_updated_by_id_user",
        "eventreferencerequest",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_eventreference_created_by_id_user"),
        "eventreference",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_eventreference_updated_by_id_user"),
        "eventreference",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_eventreference_updated_by_id_user",
        "eventreference",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_eventreference_created_by_id_user",
        "eventreference",
        "user",
        ["created_by_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_eventplace_updated_by_id_user"), "eventplace", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_eventplace_created_by_id_user"), "eventplace", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_eventplace_updated_by_id_user",
        "eventplace",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_eventplace_created_by_id_user",
        "eventplace",
        "user",
        ["created_by_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_eventorganizer_created_by_id_user"),
        "eventorganizer",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_eventorganizer_updated_by_id_user"),
        "eventorganizer",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_eventorganizer_created_by_id_user",
        "eventorganizer",
        "user",
        ["created_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_eventorganizer_updated_by_id_user",
        "eventorganizer",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_eventlist_created_by_id_user"), "eventlist", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_eventlist_updated_by_id_user"), "eventlist", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_eventlist_updated_by_id_user",
        "eventlist",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_eventlist_created_by_id_user",
        "eventlist",
        "user",
        ["created_by_id"],
        ["id"],
    )
    op.drop_constraint(op.f("fk_event_updated_by_id_user"), "event", type_="foreignkey")
    op.drop_constraint(op.f("fk_event_created_by_id_user"), "event", type_="foreignkey")
    op.create_foreign_key(
        "fk_event_created_by_id_user", "event", "user", ["created_by_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_event_updated_by_id_user", "event", "user", ["updated_by_id"], ["id"]
    )
    op.drop_constraint(
        op.f("fk_customwidget_created_by_id_user"), "customwidget", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_customwidget_updated_by_id_user"), "customwidget", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_customwidget_created_by_id_user",
        "customwidget",
        "user",
        ["created_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_customwidget_updated_by_id_user",
        "customwidget",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_adminunitrelation_created_by_id_user"),
        "adminunitrelation",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_adminunitrelation_updated_by_id_user"),
        "adminunitrelation",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_adminunitrelation_created_by_id_user",
        "adminunitrelation",
        "user",
        ["created_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_adminunitrelation_updated_by_id_user",
        "adminunitrelation",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_adminunitinvitation_created_by_id_user"),
        "adminunitinvitation",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_adminunitinvitation_updated_by_id_user"),
        "adminunitinvitation",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_adminunitinvitation_created_by_id_user",
        "adminunitinvitation",
        "user",
        ["created_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_adminunitinvitation_updated_by_id_user",
        "adminunitinvitation",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_adminunit_created_by_id_user"), "adminunit", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_adminunit_updated_by_id_user"), "adminunit", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_adminunit_updated_by_id_user",
        "adminunit",
        "user",
        ["updated_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_adminunit_created_by_id_user",
        "adminunit",
        "user",
        ["created_by_id"],
        ["id"],
    )
    # ### end Alembic commands ###
