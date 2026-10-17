import os

from project.extensions import db
from project.infrastructure.models import (
    AdminUnitMemberRole,
    EventCategory,
    Role,
    Settings,
)
from project.presentation.api import add_oauth2_scheme_with_transport


def register_oauth2_scheme_once(app):
    """Register OAuth2 scheme once on first request.

    This function should be called from create_app() to register
    a before_request handler that adds the OAuth2 scheme.
    """

    @app.before_request
    def add_oauth2_scheme():
        app.before_request_funcs[None].remove(add_oauth2_scheme)
        # At some sites the https scheme is not set yet
        insecure = os.getenv("AUTHLIB_INSECURE_TRANSPORT", "False").lower() in [
            "true",
            "1",
        ]
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


def upsert_settings() -> Settings:
    """The one settings row, created (not committed) if missing. Bootstrap and test
    seeding only; the application reads settings through `GetSettingsQuery`."""
    result = Settings.query.first()
    if result is None:
        result = Settings()
        db.session.add(result)

    return result


def _upsert_role(model_class, name, title, permissions):
    role = model_class.query.filter_by(name=name).first()

    if role is None:
        role = model_class(name=name)
        db.session.add(role)

    role.title = title
    role.permissions = permissions
    db.session.commit()


def _upsert_event_category(name):
    if EventCategory.query.filter_by(name=name).first() is None:
        db.session.add(EventCategory(name=name))
        db.session.commit()


EVENT_CATEGORY_NAMES = [
    "Art",
    "Book",
    "Movie",
    "Family",
    "Festival",
    "Religious",
    "Shopping",
    "Comedy",
    "Music",
    "Dance",
    "Nightlife",
    "Theater",
    "Dining",
    "Conference",
    "Meetup",
    "Fitness",
    "Sports",
    "Other",
    "Exhibition",
    "Culture",
    "Tour",
    "OpenAir",
    "Stage",
    "Lecture",
]


def create_initial_data():
    _upsert_role(
        AdminUnitMemberRole, "admin", "Administrator", organization_admin_permissions
    )
    _upsert_role(
        AdminUnitMemberRole,
        "event_verifier",
        "Event expert",
        organization_event_expert_permissions,
    )
    _upsert_role(Role, "admin", "Administrator", [])

    for name in EVENT_CATEGORY_NAMES:
        _upsert_event_category(name)
