"""empty message

Revision ID: cbac4166f9c0
Revises: 30650020b4b7
Create Date: 2023-04-27 11:02:04.294121

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from project import dbtypes

# revision identifiers, used by Alembic.
revision = "cbac4166f9c0"
down_revision = "30650020b4b7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE adminunit DROP CONSTRAINT IF EXISTS adminunit_name_key;")
    op.execute("ALTER TABLE adminunit DROP CONSTRAINT IF EXISTS uq_adminunit_name;")
    op.execute(
        "ALTER TABLE adminunit DROP CONSTRAINT IF EXISTS adminunit_short_name_key;"
    )
    op.execute(
        "ALTER TABLE adminunit DROP CONSTRAINT IF EXISTS uq_adminunit_short_name;"
    )

    with op.batch_alter_table("adminunit", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("deletion_requested_at", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("deletion_requested_by_id", sa.Integer(), nullable=True)
        )
        batch_op.create_unique_constraint(batch_op.f("uq_adminunit_name"), ["name"])
        batch_op.create_unique_constraint(
            batch_op.f("uq_adminunit_short_name"), ["short_name"]
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_adminunit_deletion_requested_by_id_user"),
            "user",
            ["deletion_requested_by_id"],
            ["id"],
        )

    op.execute(
        "ALTER TABLE adminunitmemberinvitation DROP CONSTRAINT IF EXISTS adminunitmemberinvitation_email_admin_unit_id_key;"
    )
    op.execute(
        "ALTER TABLE adminunitmemberinvitation DROP CONSTRAINT IF EXISTS uq_adminunitmemberinvitation_email;"
    )
    with op.batch_alter_table("adminunitmemberinvitation", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_adminunitmemberinvitation_email"), ["email", "admin_unit_id"]
        )

    op.execute(
        "ALTER TABLE adminunitmemberrole DROP CONSTRAINT IF EXISTS adminunitmemberrole_name_key;"
    )
    op.execute(
        "ALTER TABLE adminunitmemberrole DROP CONSTRAINT IF EXISTS uq_adminunitmemberrole_name;"
    )
    with op.batch_alter_table("adminunitmemberrole", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_adminunitmemberrole_name"), ["name"]
        )

    op.execute(
        "ALTER TABLE adminunitrelation DROP CONSTRAINT IF EXISTS adminunitrelation_source_admin_unit_id_target_admin_unit_id_key;"
    )
    op.execute(
        "ALTER TABLE adminunitrelation DROP CONSTRAINT IF EXISTS uq_adminunitrelation_source_admin_unit_id;"
    )
    with op.batch_alter_table("adminunitrelation", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_adminunitrelation_source_admin_unit_id"),
            ["source_admin_unit_id", "target_admin_unit_id"],
        )

    op.execute(
        "ALTER TABLE event_coorganizers DROP CONSTRAINT IF EXISTS event_coorganizers_event_id_organizer_id_key;"
    )
    op.execute(
        "ALTER TABLE event_coorganizers DROP CONSTRAINT IF EXISTS uq_event_coorganizers_event_id;"
    )
    with op.batch_alter_table("event_coorganizers", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_event_coorganizers_event_id"), ["event_id", "organizer_id"]
        )

    op.execute(
        "ALTER TABLE event_eventcategories DROP CONSTRAINT IF EXISTS event_eventcategories_event_id_category_id;"
    )
    op.execute(
        "ALTER TABLE event_eventcategories DROP CONSTRAINT IF EXISTS event_eventcategories_event_id_category_id_key;"
    )
    op.execute(
        "ALTER TABLE event_eventcategories DROP CONSTRAINT IF EXISTS uq_event_eventcategories_event_id;"
    )

    with op.batch_alter_table("event_eventcategories", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_event_eventcategories_event_id"), ["event_id", "category_id"]
        )

    op.execute(
        "ALTER TABLE event_eventlists DROP CONSTRAINT IF EXISTS event_eventlists_event_id_list_id_key;"
    )
    op.execute(
        "ALTER TABLE event_eventlists DROP CONSTRAINT IF EXISTS uq_event_eventlists_event_id;"
    )
    with op.batch_alter_table("event_eventlists", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_event_eventlists_event_id"), ["event_id", "list_id"]
        )

    op.execute(
        "ALTER TABLE eventcategory DROP CONSTRAINT IF EXISTS eventcategory_name_key;"
    )
    op.execute(
        "ALTER TABLE eventcategory DROP CONSTRAINT IF EXISTS uq_eventcategory_name;"
    )
    with op.batch_alter_table("eventcategory", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_eventcategory_name"), ["name"])

    op.execute(
        "ALTER TABLE eventorganizer DROP CONSTRAINT IF EXISTS eventorganizer_name_admin_unit_id_key;"
    )
    op.execute(
        "ALTER TABLE eventorganizer DROP CONSTRAINT IF EXISTS uq_eventorganizer_name;"
    )
    with op.batch_alter_table("eventorganizer", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_eventorganizer_name"), ["name", "admin_unit_id"]
        )

    op.execute(
        "ALTER TABLE eventplace DROP CONSTRAINT IF EXISTS eventplace_name_admin_unit_id;"
    )
    op.execute(
        "ALTER TABLE eventplace DROP CONSTRAINT IF EXISTS eventplace_name_admin_unit_id_key;"
    )
    op.execute("ALTER TABLE eventplace DROP CONSTRAINT IF EXISTS uq_eventplace_name;")
    with op.batch_alter_table("eventplace", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_eventplace_name"), ["name", "admin_unit_id"]
        )

    op.execute(
        "ALTER TABLE eventsuggestion_eventcategories DROP CONSTRAINT IF EXISTS eventsuggestion_eventcategori_event_suggestion_id_category__key;"
    )
    op.execute(
        "ALTER TABLE eventsuggestion_eventcategories DROP CONSTRAINT IF EXISTS eventsuggestion_eventcategories_event_suggestion_id_category_id;"
    )
    op.execute(
        "ALTER TABLE eventsuggestion_eventcategories DROP CONSTRAINT IF EXISTS uq_eventsuggestion_eventcategories_event_suggestion_id;"
    )
    with op.batch_alter_table(
        "eventsuggestion_eventcategories", schema=None
    ) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_eventsuggestion_eventcategories_event_suggestion_id"),
            ["event_suggestion_id", "category_id"],
        )

    op.execute(
        "ALTER TABLE flask_dance_oauth DROP CONSTRAINT IF EXISTS flask_dance_oauth_provider_user_id_key;"
    )
    op.execute(
        "ALTER TABLE flask_dance_oauth DROP CONSTRAINT IF EXISTS uq_flask_dance_oauth_provider_user_id;"
    )
    with op.batch_alter_table("flask_dance_oauth", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_flask_dance_oauth_provider_user_id"), ["provider_user_id"]
        )

    op.execute(
        "ALTER TABLE oauth2_code DROP CONSTRAINT IF EXISTS oauth2_code_code_key;"
    )
    op.execute("ALTER TABLE oauth2_code DROP CONSTRAINT IF EXISTS uq_oauth2_code_code;")
    with op.batch_alter_table("oauth2_code", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_oauth2_code_code"), ["code"])

    op.execute(
        "ALTER TABLE oauth2_token DROP CONSTRAINT IF EXISTS oauth2_token_access_token_key;"
    )
    op.execute(
        "ALTER TABLE oauth2_token DROP CONSTRAINT IF EXISTS uq_oauth2_token_access_token;"
    )
    with op.batch_alter_table("oauth2_token", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_oauth2_token_access_token"), ["access_token"]
        )

    op.execute("ALTER TABLE role DROP CONSTRAINT IF EXISTS role_name_key;")
    op.execute("ALTER TABLE role DROP CONSTRAINT IF EXISTS uq_role_name;")
    with op.batch_alter_table("role", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_role_name"), ["name"])

    op.execute("ALTER TABLE public.user DROP CONSTRAINT IF EXISTS user_email_key;")
    op.execute("ALTER TABLE public.user DROP CONSTRAINT IF EXISTS uq_user_email;")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f("uq_user_email"), ["email"])

    op.execute(
        "ALTER TABLE user_favoriteevents DROP CONSTRAINT IF EXISTS user_favoriteevents_user_id_event_id_key;"
    )
    op.execute(
        "ALTER TABLE user_favoriteevents DROP CONSTRAINT IF EXISTS uq_user_favoriteevents_user_id;"
    )
    with op.batch_alter_table("user_favoriteevents", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_user_favoriteevents_user_id"), ["user_id", "event_id"]
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user_favoriteevents", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_user_favoriteevents_user_id"), type_="unique"
        )
        batch_op.create_unique_constraint(
            "user_favoriteevents_user_id_event_id_key", ["user_id", "event_id"]
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_user_email"), type_="unique")
        batch_op.create_unique_constraint("user_email_key", ["email"])

    with op.batch_alter_table("role", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_role_name"), type_="unique")
        batch_op.create_unique_constraint("role_name_key", ["name"])

    with op.batch_alter_table("oauth2_token", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_oauth2_token_access_token"), type_="unique"
        )
        batch_op.create_unique_constraint(
            "oauth2_token_access_token_key", ["access_token"]
        )

    with op.batch_alter_table("oauth2_code", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_oauth2_code_code"), type_="unique")
        batch_op.create_unique_constraint("oauth2_code_code_key", ["code"])

    with op.batch_alter_table("flask_dance_oauth", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_flask_dance_oauth_provider_user_id"), type_="unique"
        )
        batch_op.create_unique_constraint(
            "flask_dance_oauth_provider_user_id_key", ["provider_user_id"]
        )

    with op.batch_alter_table(
        "eventsuggestion_eventcategories", schema=None
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_eventsuggestion_eventcategories_event_suggestion_id"),
            type_="unique",
        )
        batch_op.create_unique_constraint(
            "eventsuggestion_eventcategori_event_suggestion_id_category__key",
            ["event_suggestion_id", "category_id"],
        )

    with op.batch_alter_table("eventplace", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_eventplace_name"), type_="unique")
        batch_op.create_unique_constraint(
            "eventplace_name_admin_unit_id_key", ["name", "admin_unit_id"]
        )

    with op.batch_alter_table("eventorganizer", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_eventorganizer_name"), type_="unique")
        batch_op.create_unique_constraint(
            "eventorganizer_name_admin_unit_id_key", ["name", "admin_unit_id"]
        )

    with op.batch_alter_table("eventcategory", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_eventcategory_name"), type_="unique")
        batch_op.create_unique_constraint("eventcategory_name_key", ["name"])

    with op.batch_alter_table("event_eventlists", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_event_eventlists_event_id"), type_="unique"
        )
        batch_op.create_unique_constraint(
            "event_eventlists_event_id_list_id_key", ["event_id", "list_id"]
        )

    with op.batch_alter_table("event_eventcategories", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_event_eventcategories_event_id"), type_="unique"
        )
        batch_op.create_unique_constraint(
            "event_eventcategories_event_id_category_id_key",
            ["event_id", "category_id"],
        )

    with op.batch_alter_table("event_coorganizers", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_event_coorganizers_event_id"), type_="unique"
        )
        batch_op.create_unique_constraint(
            "event_coorganizers_event_id_organizer_id_key", ["event_id", "organizer_id"]
        )

    with op.batch_alter_table("adminunitrelation", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_adminunitrelation_source_admin_unit_id"), type_="unique"
        )
        batch_op.create_unique_constraint(
            "adminunitrelation_source_admin_unit_id_target_admin_unit_id_key",
            ["source_admin_unit_id", "target_admin_unit_id"],
        )

    with op.batch_alter_table("adminunitmemberrole", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_adminunitmemberrole_name"), type_="unique"
        )
        batch_op.create_unique_constraint("adminunitmemberrole_name_key", ["name"])

    with op.batch_alter_table("adminunitmemberinvitation", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_adminunitmemberinvitation_email"), type_="unique"
        )
        batch_op.create_unique_constraint(
            "adminunitmemberinvitation_email_admin_unit_id_key",
            ["email", "admin_unit_id"],
        )

    with op.batch_alter_table("adminunit", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_adminunit_deletion_requested_by_id_user"), type_="foreignkey"
        )
        batch_op.drop_constraint(batch_op.f("uq_adminunit_short_name"), type_="unique")
        batch_op.drop_constraint(batch_op.f("uq_adminunit_name"), type_="unique")
        batch_op.create_unique_constraint("adminunit_short_name_key", ["short_name"])
        batch_op.create_unique_constraint("adminunit_name_key", ["name"])
        batch_op.drop_column("deletion_requested_by_id")
        batch_op.drop_column("deletion_requested_at")

    # ### end Alembic commands ###
