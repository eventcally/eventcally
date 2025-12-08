import os

from project import app, db
from project.api import add_oauth2_scheme_with_transport
from project.models import Location


@app.before_request
def add_oauth2_scheme():
    app.before_request_funcs[None].remove(add_oauth2_scheme)
    # At some sites the https scheme is not set yet
    insecure = os.getenv("AUTHLIB_INSECURE_TRANSPORT", "False").lower() in ["true", "1"]
    add_oauth2_scheme_with_transport(insecure)


organization_admin_permissions = [
    "api_keys:read",
    "api_keys:write",
    "apps:read",
    "apps:write",
    "app_keys:read",
    "app_keys:write",
    "app_installations:read",
    "app_installations:write",
    "custom_widgets:read",
    "custom_widgets:write",
    "export:read",
    "incoming_organization_verification_requests:read",
    "incoming_organization_verification_requests:write",
    "oauth2_clients:read",
    "oauth2_clients:write",
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
    organization_member_role_service = (
        app.container.services.organization_member_role_service()
    )
    organization_member_role_service.upsert_role(
        "admin", "Administrator", organization_admin_permissions
    )
    organization_member_role_service.upsert_role(
        "event_verifier", "Event expert", organization_event_expert_permissions
    )

    role_service = app.container.services.role_service()
    role_service.upsert_role("admin", "Administrator", [])

    Location.update_coordinates()
    db.session.commit()

    event_category_service = app.container.services.event_category_service()
    event_category_service.upsert_event_category("Art")
    event_category_service.upsert_event_category("Book")
    event_category_service.upsert_event_category("Movie")
    event_category_service.upsert_event_category("Family")
    event_category_service.upsert_event_category("Festival")
    event_category_service.upsert_event_category("Religious")
    event_category_service.upsert_event_category("Shopping")
    event_category_service.upsert_event_category("Comedy")
    event_category_service.upsert_event_category("Music")
    event_category_service.upsert_event_category("Dance")
    event_category_service.upsert_event_category("Nightlife")
    event_category_service.upsert_event_category("Theater")
    event_category_service.upsert_event_category("Dining")
    event_category_service.upsert_event_category("Conference")
    event_category_service.upsert_event_category("Meetup")
    event_category_service.upsert_event_category("Fitness")
    event_category_service.upsert_event_category("Sports")
    event_category_service.upsert_event_category("Other")
    event_category_service.upsert_event_category("Exhibition")
    event_category_service.upsert_event_category("Culture")
    event_category_service.upsert_event_category("Tour")
    event_category_service.upsert_event_category("OpenAir")
    event_category_service.upsert_event_category("Stage")
    event_category_service.upsert_event_category("Lecture")
