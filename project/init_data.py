from project import app, db
from project.services.user import upsert_user_role, add_admin_roles_to_user
from project.services.admin_unit import upsert_admin_unit_member_role
from project.services.event import upsert_event_category
from project.models import Location


@app.before_first_request
def create_initial_data():
    admin_permissions = [
        "admin_unit:update",
        "admin_unit.members:invite",
        "admin_unit.members:read",
        "admin_unit.members:update",
        "admin_unit.members:delete",
    ]
    event_permissions = [
        "event:verify",
        "event:create",
        "event:read",
        "event:update",
        "event:delete",
        "event:reference",
        "event_suggestion:read",
        "organizer:create",
        "organizer:update",
        "organizer:delete",
        "place:create",
        "place:update",
        "place:delete",
        "reference:update",
        "reference:delete",
        "reference_request:create",
        "reference_request:read",
        "reference_request:update",
        "reference_request:delete",
        "reference_request:verify",
    ]

    upsert_admin_unit_member_role("admin", "Administrator", admin_permissions)
    upsert_admin_unit_member_role("event_verifier", "Event expert", event_permissions)

    upsert_user_role("admin", "Administrator", admin_permissions)
    upsert_user_role("event_verifier", "Event expert", event_permissions)
    add_admin_roles_to_user("grams.daniel@gmail.com")

    Location.update_coordinates()

    upsert_event_category("Art")
    upsert_event_category("Book")
    upsert_event_category("Movie")
    upsert_event_category("Family")
    upsert_event_category("Festival")
    upsert_event_category("Religious")
    upsert_event_category("Shopping")
    upsert_event_category("Comedy")
    upsert_event_category("Music")
    upsert_event_category("Dance")
    upsert_event_category("Nightlife")
    upsert_event_category("Theater")
    upsert_event_category("Dining")
    upsert_event_category("Conference")
    upsert_event_category("Meetup")
    upsert_event_category("Fitness")
    upsert_event_category("Sports")
    upsert_event_category("Other")

    db.session.commit()
