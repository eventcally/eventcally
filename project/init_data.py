from project import app, db
from project.api import api_docs, scopes
from project.services.user import upsert_user_role
from project.services.admin_unit import upsert_admin_unit_member_role
from project.services.event import upsert_event_category
from project.models import Location
from flask import url_for
from apispec.exceptions import DuplicateComponentNameError


@app.before_first_request
def add_oauth2_scheme():
    oauth2_scheme = {
        "type": "oauth2",
        "authorizationUrl": url_for("authorize", _external=True),
        "tokenUrl": url_for("issue_token", _external=True),
        "flow": "accessCode",
        "scopes": scopes,
    }

    try:
        api_docs.spec.components.security_scheme("oauth2", oauth2_scheme)
    except DuplicateComponentNameError:  # pragma: no cover
        pass


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
        "reference:read",
        "reference:update",
        "reference:delete",
        "reference_request:create",
        "reference_request:read",
        "reference_request:update",
        "reference_request:delete",
        "reference_request:verify",
    ]
    early_adopter_permissions = [
        "oauth2_client:create",
        "oauth2_client:read",
        "oauth2_client:update",
        "oauth2_client:delete",
        "oauth2_token:create",
        "oauth2_token:read",
        "oauth2_token:update",
        "oauth2_token:delete",
    ]

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
