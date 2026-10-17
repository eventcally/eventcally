"""Access decisions of the API and the manage pages, per actor.

`data/access_decision_matrix.json` holds the status codes captured on the ORM access
path (`UPDATE_READ_PARITY=1`), before the access checks moved onto the permission port.
It is the safety net of that move: every cell is one actor doing one thing.
"""

import json
import os
from pathlib import Path

from tests.integration.event_read_seed import seed_event_world
from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions

SNAPSHOT_PATH = Path(__file__).parent / "data" / "access_decision_matrix.json"


def _credentials(utils: UtilActions):
    credentials = (utils._access_token, utils._api_key)
    utils._access_token = None
    utils._api_key = None
    return credentials


def _build_actors(app, db, seeder: Seeder, utils: UtilActions):
    """name → (api credentials, web login email or None)."""
    ids = seed_event_world(app, db, seeder)
    owner_a = seeder.get_admin_unit_owner_id(ids["a"])
    owner_b = seeder.get_admin_unit_owner_id(ids["b"])
    utils.logout()
    _credentials(utils)

    actors = {"anonymous": ((None, None), None)}

    seeder.authorize_api_access(owner_a, ids["a"])
    actors["owner_a"] = (_credentials(utils), "test@test.de")

    seeder.create_admin_unit_member(ids["a"], ["event_verifier"], "verifier@test.de")
    from project.infrastructure.user_datastore import find_user_by_email

    with app.app_context():
        verifier_id = find_user_by_email("verifier@test.de").id
    _, verifier_key = seeder.insert_default_api_key(verifier_id)
    actors["verifier_a"] = ((None, verifier_key), "verifier@test.de")

    seeder.authorize_api_access(owner_b, ids["b"])
    actors["owner_b"] = (_credentials(utils), "other@test.de")

    admin_id = seeder.create_user("platform@test.de", admin=True)
    seeder.authorize_api_access(admin_id, ids["a"])
    actors["platform_admin"] = (_credentials(utils), "platform@test.de")

    seeder.authorize_api_access_as_app_installation(ids["a"])
    actors["installation_a"] = (_credentials(utils), None)

    seeder.authorize_api_access_as_app_installation(ids["b"])
    actors["installation_b"] = (_credentials(utils), None)

    _, key = seeder.insert_default_api_key(owner_a)
    actors["api_key_owner_a"] = ((None, key), None)

    with app.app_context():
        from project.infrastructure.models import EventOrganizer, EventPlace

        ids["organizer_a"] = (
            EventOrganizer.query.filter_by(admin_unit_id=ids["a"]).first().id
        )
        ids["organizer_b"] = (
            EventOrganizer.query.filter_by(admin_unit_id=ids["b"]).first().id
        )
        ids["place_a"] = EventPlace.query.filter_by(admin_unit_id=ids["a"]).first().id

    return ids, actors


def _api_requests(utils: UtilActions, ids):
    def url(endpoint, **kwargs):
        return utils.get_url(endpoint, **kwargs)

    return {
        "get_draft_event": ("GET", url("api_v1_event", id=ids["draft"]), None),
        "get_planned_event": ("GET", url("api_v1_event", id=ids["planned"]), None),
        "get_unverified_event": (
            "GET",
            url("api_v1_event", id=ids["unverified"]),
            None,
        ),
        "list_events_a": (
            "GET",
            url("api_v1_organization_event_list", id=ids["a"]),
            None,
        ),
        "list_unverified_events": (
            "GET",
            url("api_v1_organization_event_list", id=ids["c"]),
            None,
        ),
        "search_events_a": (
            "GET",
            url("api_v1_organization_event_search", id=ids["a"]),
            None,
        ),
        "patch_event": (
            "PATCH",
            url("api_v1_event", id=ids["full"]),
            {"name": "Patched event"},
        ),
        "patch_foreign_event": (
            "PATCH",
            url("api_v1_event", id=ids["other"]),
            {"name": "Patched event"},
        ),
        "patch_unknown_event": ("PATCH", url("api_v1_event", id=4711), {"name": "xyz"}),
        "patch_organizer": (
            "PATCH",
            url("api_v1_organizer", id=ids["organizer_a"]),
            {"name": "Patched organizer"},
        ),
        "patch_foreign_organizer": (
            "PATCH",
            url("api_v1_organizer", id=ids["organizer_b"]),
            {"name": "Patched organizer"},
        ),
        "patch_place": (
            "PATCH",
            url("api_v1_place", id=ids["place_a"]),
            {"name": "Patched place"},
        ),
        "create_event": (
            "POST",
            url("api_v1_organization_event_list", id=ids["a"]),
            {},
        ),
        "create_organizer": (
            "POST",
            url("api_v1_organization_organizer_list", id=ids["a"]),
            {},
        ),
        "create_place": (
            "POST",
            url("api_v1_organization_place_list", id=ids["a"]),
            {},
        ),
        "create_in_unknown_organization": (
            "POST",
            url("api_v1_organization_place_list", id=4711),
            {},
        ),
        "incoming_reference_requests": (
            "GET",
            url(
                "api_v1_organization_incoming_event_reference_request_list", id=ids["a"]
            ),
            None,
        ),
        "outgoing_reference_requests": (
            "GET",
            url(
                "api_v1_organization_outgoing_event_reference_request_list", id=ids["a"]
            ),
            None,
        ),
        "incoming_references": (
            "GET",
            url("api_v1_organization_incoming_event_reference_list", id=ids["a"]),
            None,
        ),
        "organization_invitations": (
            "GET",
            url("api_v1_organization_organization_invitation_list", id=ids["a"]),
            None,
        ),
        "custom_widgets": (
            "GET",
            url("api_v1_organization_custom_widget_list", id=ids["a"]),
            None,
        ),
        "organization_with_settings": (
            "GET",
            url("api_v1_organization", id=ids["a"]),
            None,
        ),
    }


def _web_requests(utils: UtilActions, ids):
    def url(endpoint, **kwargs):
        return utils.get_url(endpoint, **kwargs)

    return {
        "manage_events": url("manage_admin_unit.events", id=ids["a"]),
        "manage_event_create": url("manage_admin_unit.event_create", id=ids["a"]),
        "manage_members": url("manage_admin_unit.organization_members", id=ids["a"]),
        "manage_api_keys": url("manage_admin_unit.api_keys", id=ids["a"]),
        "manage_settings": url("manage_admin_unit.update", id=ids["a"]),
        "manage_other_organization": url("manage_admin_unit.events", id=ids["b"]),
        "manage_unknown_organization": url("manage_admin_unit.events", id=4711),
        "manage_event_update": url(
            "manage_admin_unit.event_update", id=ids["a"], event_id=ids["full"]
        ),
        "main_draft_event": url("main.event", event_id=ids["draft"]),
        "main_planned_event": url("main.event", event_id=ids["planned"]),
        "main_planning": url("main.planning"),
        "main_event_actions": url("main.event_actions", event_id=ids["full"]),
        "main_event_reference": url(
            "main.event_reference_create", event_id=ids["other"]
        ),
    }


def test_access_decisions_match_snapshot(client, app, db, seeder, utils):
    app.config["API_READ_ANONYM"] = True
    ids, actors = _build_actors(app, db, seeder, utils)
    api_requests = _api_requests(utils, ids)
    web_requests = _web_requests(utils, ids)
    actual = {}

    for name, ((token, api_key), email) in actors.items():
        for key, (method, url, body) in api_requests.items():
            utils._access_token = token
            utils._api_key = api_key
            from project.extensions import limiter

            with app.app_context():
                limiter.reset()

            response = getattr(client, method.lower())(
                url,
                headers=utils.get_headers(),
                **({"json": body} if body is not None else {}),
            )
            actual[f"{name}:api:{key}"] = response.status_code

        utils._access_token = None
        utils._api_key = None

        if email:
            utils.login(email)

            for key, url in web_requests.items():
                actual[f"{name}:web:{key}"] = client.get(url).status_code

            utils.logout()
        else:
            for key, url in web_requests.items():
                actual[f"{name}:web:{key}"] = client.get(url).status_code

    if os.environ.get("UPDATE_READ_PARITY") == "1":  # pragma: no cover
        SNAPSHOT_PATH.write_text(json.dumps(actual, indent=1, sort_keys=True) + "\n")
        return

    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert sorted(actual) == sorted(expected)
    mismatches = {
        key: (expected[key], actual[key])
        for key in sorted(expected)
        if actual[key] != expected[key]
    }
    if mismatches and os.environ.get("PARITY_DIFF_FILE"):  # pragma: no cover
        Path(os.environ["PARITY_DIFF_FILE"]).write_text(json.dumps(actual, indent=1))

    assert mismatches == {}
