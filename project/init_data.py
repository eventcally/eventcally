import os

from project import app, db
from project.api import add_oauth2_scheme_with_transport
from project.models import Location
from project.services.admin_unit import upsert_admin_unit_member_role
from project.services.event import upsert_event_category
from project.services.user import upsert_user_role


@app.before_request
def add_oauth2_scheme():
    app.before_request_funcs[None].remove(add_oauth2_scheme)
    # At some sites the https scheme is not set yet
    insecure = os.getenv("AUTHLIB_INSECURE_TRANSPORT", "False").lower() in ["true", "1"]
    add_oauth2_scheme_with_transport(insecure)


organization_admin_permissions = [
    "api_keys:read",
    "api_keys:write",
    "custom_widgets:read",
    "custom_widgets:write",
    "export:read",
    "incoming_organization_verification_requests:read",
    "incoming_organization_verification_requests:write",
    "organization_invitations:read",
    "organization_invitations:write",
    "organization_member_invitations:read",
    "organization_member_invitations:write",
    "organization_members:read",
    "organization_members:write",
    "outgoing_organization_relations:read",
    "outgoing_organization_relations:write",
    "outgoing_organization_verification_requests:read",
    "outgoing_organization_verification_requests:write",
    "settings:read",
    "settings:write",
    "widgets:read",
    "widgets:write",
]
organization_event_expert_permissions = [
    "event_lists:read",
    "event_lists:write",
    "event_organizers:read",
    "event_organizers:write",
    "event_places:read",
    "event_places:write",
    "events:read",
    "events:write",
    "incoming_event_reference_requests:read",
    "incoming_event_reference_requests:write",
    "incoming_event_references:read",
    "incoming_event_references:write",
    "outgoing_event_reference_requests:read",
    "outgoing_event_reference_requests:write",
    "outgoing_event_references:read",
    "outgoing_event_references:write",
]


def create_initial_data():
    upsert_admin_unit_member_role(
        "admin", "Administrator", organization_admin_permissions
    )
    upsert_admin_unit_member_role(
        "event_verifier", "Event expert", organization_event_expert_permissions
    )

    upsert_user_role("admin", "Administrator", [])

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
