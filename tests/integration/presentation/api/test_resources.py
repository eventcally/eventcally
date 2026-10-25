"""The public API authenticates with OAuth tokens or API keys only; a site session
(cookie, with or without a CSRF token) grants nothing on /api/v1."""

import pytest


@pytest.fixture
def session_with_csrf(seeder, utils):
    """A logged-in site session whose CSRF token is sent as X-CSRFToken (no bearer)."""
    user_id, admin_unit_id = seeder.setup_base(admin_unit_verified=False)
    utils.get_ok(utils.get_url("main.manage_admin_units"))
    assert utils.get_headers().get("X-CSRFToken")
    return user_id, admin_unit_id


def test_session_with_csrf_token_is_unauthorized(app, utils, session_with_csrf):
    app.config["API_READ_ANONYM"] = False

    response = utils.get_json(utils.get_url("api_v1_organization_list"))
    utils.assert_response_unauthorized(response)


def test_session_with_csrf_token_reads_anonymous(app, utils, session_with_csrf):
    _, admin_unit_id = session_with_csrf
    app.config["API_READ_ANONYM"] = True

    # The user's own organization is unverified: only visible to its members.
    response = utils.get_json_ok(utils.get_url("api_v1_organization_list"))
    assert admin_unit_id not in [item["id"] for item in response.json["items"]]


def test_session_with_csrf_token_cannot_write(app, utils, session_with_csrf):
    _, admin_unit_id = session_with_csrf

    for anonymous_reads in (False, True):
        app.config["API_READ_ANONYM"] = anonymous_reads
        response = utils.post_json(
            utils.get_url("api_v1_organization_event_list", id=admin_unit_id),
            {"name": "Name", "start": "2030-12-31T14:00:00"},
        )
        utils.assert_response_unauthorized(response)


def test_token_response_sets_no_session_cookie(client, seeder, utils):
    seeder.setup_api_access(user_access=True)
    client.delete_cookie("session")

    response = utils.get_json(utils.get_url("api_v1_organization_list"))
    utils.assert_response_ok(response)
    assert "session=" not in ";".join(response.headers.getlist("Set-Cookie"))


def test_api_call_keeps_site_session(app, utils, session_with_csrf):
    app.config["API_READ_ANONYM"] = True
    utils.get_json_ok(utils.get_url("api_v1_organization_list"))

    utils.get_ok(utils.get_url("main.manage_admin_units"))


def test_app_endpoints_require_an_app_token(app, utils):
    app.config["API_READ_ANONYM"] = True

    response = utils.get_json(utils.get_url("api_v1_app_installation_list"))
    utils.assert_response_unauthorized(response)
