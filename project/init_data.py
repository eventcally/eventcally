import os

from project import app, db
from project.api import add_oauth2_scheme_with_transport
from project.models import Location
from project.services.admin_unit import upsert_admin_unit_member_role
from project.services.event import upsert_event_category
from project.services.user import upsert_user_role


@app.before_first_request
def add_oauth2_scheme():
    # At some sites the https scheme is not set yet
    insecure = os.getenv("AUTHLIB_INSECURE_TRANSPORT", "False").lower() in ["true", "1"]
    add_oauth2_scheme_with_transport(insecure)


@app.before_first_request
def create_initial_data():
    admin_permissions = [
        "admin_unit:update",
        "admin_unit.members:invite",
        "admin_unit.members:read",
        "admin_unit.members:update",
        "admin_unit.members:delete",
        "verification_request:create",
        "verification_request:read",
        "verification_request:update",
        "verification_request:delete",
        "verification_request:verify",
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
        "reference:read",
        "reference:update",
        "reference:delete",
        "reference_request:create",
        "reference_request:read",
        "reference_request:update",
        "reference_request:delete",
        "reference_request:verify",
    ]
    early_adopter_permissions = []

    upsert_admin_unit_member_role("admin", "Administrator", admin_permissions)
    upsert_admin_unit_member_role("event_verifier", "Event expert", event_permissions)

    upsert_user_role("admin", "Administrator", admin_permissions)
    upsert_user_role("event_verifier", "Event expert", event_permissions)
    upsert_user_role("early_adopter", "Early Adopter", early_adopter_permissions)

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
    upsert_event_category("Exhibition")
    upsert_event_category("Culture")
    upsert_event_category("Tour")
    upsert_event_category("OpenAir")
    upsert_event_category("Stage")
    upsert_event_category("Lecture")

    db.session.commit()
