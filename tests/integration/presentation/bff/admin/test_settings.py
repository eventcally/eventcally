def _login_admin(seeder, utils):
    seeder.create_user(admin=True)
    utils.login()
    utils.get_ok("/admin/settings")  # picks up the CSRF token of the Vue 3 shell


def _put(utils, key, value):
    return utils.put_json(f"/bff/admin/settings/{key}", {"value": value})


def test_settings_empty(client, seeder, utils):
    _login_admin(seeder, utils)

    body = utils.get_json_ok("/bff/admin/settings").json

    assert body == {
        "start_page": None,
        "tos": None,
        "legal_notice": None,
        "contact": None,
        "privacy": None,
        "announcement": None,
    }


def test_update_setting(client, seeder, utils):
    _login_admin(seeder, utils)

    utils.assert_response_no_content(_put(utils, "legal_notice", "<p>Impressum</p>"))
    utils.assert_response_no_content(_put(utils, "tos", "<p>Terms</p>"))

    body = utils.get_json_ok("/bff/admin/settings").json
    assert body["tos"] == "<p>Terms</p>"
    assert body["legal_notice"] == "<p>Impressum</p>"
    assert body["announcement"] is None


def test_update_setting_each_key(client, seeder, utils):
    _login_admin(seeder, utils)

    for key in [
        "start_page",
        "tos",
        "legal_notice",
        "contact",
        "privacy",
        "announcement",
    ]:
        utils.assert_response_no_content(_put(utils, key, f"v-{key}"))

    body = utils.get_json_ok("/bff/admin/settings").json
    assert body == {k: f"v-{k}" for k in body}


def test_update_setting_blank_clears(client, seeder, utils):
    _login_admin(seeder, utils)
    _put(utils, "contact", "x")

    utils.assert_response_no_content(_put(utils, "contact", "  "))

    assert utils.get_json_ok("/bff/admin/settings").json["contact"] is None


def test_update_setting_unknown_key(client, seeder, utils):
    _login_admin(seeder, utils)

    response = _put(utils, "planning_external_calendars", "x")

    utils.assert_response_notFound(response)
    assert response.json["name"] == "Not Found"


def test_update_setting_missing_value(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.put_json("/bff/admin/settings/tos", {})

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["value"]


def test_update_setting_forbidden(client, seeder, utils):
    seeder.create_user()
    utils.login()
    utils.get_ok("/")

    response = _put(utils, "tos", "x")

    utils.assert_response_forbidden(response)


def test_update_setting_without_csrf(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    utils.assert_response_bad_request(_put(utils, "tos", "x"))


def test_settings_forbidden(client, seeder, utils):
    seeder.create_user()
    utils.login()

    response = utils.get_json("/bff/admin/settings")

    utils.assert_response_forbidden(response)
    assert response.json["name"] == "Forbidden"


def test_settings_unauthorized(client, utils):
    utils.assert_response_unauthorized(utils.get_json("/bff/admin/settings"))


def test_planning(client, seeder, utils):
    _login_admin(seeder, utils)
    raw = '[{"title":"a","url":"https://x","active":true}]'

    response = utils.put_json(
        "/bff/admin/planning", {"planning_external_calendars": raw}
    )

    utils.assert_response_ok(response)
    assert "\n  " in response.json["planning_external_calendars"]
    body = utils.get_json_ok("/bff/admin/planning").json
    assert body == response.json


def test_planning_invalid_json(client, seeder, utils):
    _login_admin(seeder, utils)
    utils.put_json("/bff/admin/planning", {"planning_external_calendars": "[]"})

    response = utils.put_json(
        "/bff/admin/planning", {"planning_external_calendars": "{"}
    )

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["planning_external_calendars"]
    assert utils.get_json_ok("/bff/admin/planning").json == {
        "planning_external_calendars": "[]"
    }


def test_planning_clear(client, seeder, utils):
    _login_admin(seeder, utils)
    utils.put_json("/bff/admin/planning", {"planning_external_calendars": "[]"})

    response = utils.put_json(
        "/bff/admin/planning", {"planning_external_calendars": None}
    )

    utils.assert_response_ok(response)
    assert response.json["planning_external_calendars"] is None


def test_planning_forbidden(client, seeder, utils):
    seeder.create_user()
    utils.login()

    utils.assert_response_forbidden(utils.get_json("/bff/admin/planning"))


def test_reset_tos_accepted(app, client, seeder, utils):
    from project.infrastructure.user_datastore import find_user_by_email

    _login_admin(seeder, utils)
    seeder.create_user(email="other@test.de")
    with app.app_context():
        assert find_user_by_email("other@test.de").tos_accepted_at is not None

    response = utils.post_json("/bff/admin/settings/reset-tos-accepted", None)

    utils.assert_response_no_content(response)
    with app.app_context():
        assert find_user_by_email("other@test.de").tos_accepted_at is None


def test_reset_tos_accepted_forbidden(client, seeder, utils):
    seeder.create_user()
    utils.login()
    utils.get_ok("/")

    response = utils.post_json("/bff/admin/settings/reset-tos-accepted", None)

    utils.assert_response_forbidden(response)
