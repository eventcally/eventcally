from project import app, db
from project.services.user import upsert_user_role, add_roles_to_user
from project.services.admin_unit import upsert_admin_unit_member_role
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
    add_roles_to_user("grams.daniel@gmail.com", ["admin", "event_verifier"])

    Location.update_coordinates()

    db.session.commit()
