import pytest

BASE_URL = "/bff/manage/organizations/{}/widget-settings"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/widgets")


def _colors(app, db, admin_unit_id):
    with app.app_context():
        from project.infrastructure.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        return (
            admin_unit.widget_font,
            admin_unit.widget_background_color
            and admin_unit.widget_background_color.hex_l,
            admin_unit.widget_primary_color and admin_unit.widget_primary_color.hex_l,
            admin_unit.widget_link_color and admin_unit.widget_link_color.hex_l,
        )


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    base = BASE_URL.format(seeder.create_admin_unit(owner_id))

    assert utils.get_json(base).status_code == 401
    assert utils.put_json(base, dict()).status_code == 401


def test_member_without_permission_is_403(client, seeder, utils):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()
    utils.get_ok("/organizations")
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(base).status_code == 403
    assert utils.put_json(base, dict()).status_code == 403


def test_other_organization_is_403(client, seeder, utils):
    owner_id = seeder.create_user(email="owner@test.de")
    admin_unit_id = seeder.create_admin_unit(owner_id, name="Fremde Crew")
    seeder.create_user()
    utils.login()

    assert utils.get_json(BASE_URL.format(admin_unit_id)).status_code == 403


def test_unknown_organization_is_404(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    assert utils.get_json(BASE_URL.format(9999)).status_code == 404


# read


def test_get_defaults(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    data = utils.get_json_ok(BASE_URL.format(admin_unit_id)).json

    assert data["id"] == admin_unit_id
    assert data["font"] == ""
    assert data["background_color"] == "#ffffff"
    assert data["primary_color"] == "#007bff"
    assert data["link_color"] == "#007bff"
    assert data["loader_url"].endswith("/static/widget-loader.js")
    assert data["loader_url"].startswith("http")
    assert data["iframe_url"].startswith("http")
    assert data["iframe_url"].endswith(
        f"/organizations/{admin_unit_id}/widget/eventdates"
    )
    assert data["preview_url"] == f"/organizations/{admin_unit_id}/widget/eventdates"


# write


def test_put_requires_csrf(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    response = utils.put_json(BASE_URL.format(admin_unit_id), dict())

    assert response.status_code == 400


def test_put_stores_colors_and_loads_them_again(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    base = BASE_URL.format(admin_unit_id)

    # The second save loads the stored colors through the organization aggregate.
    for _ in range(2):
        response = utils.put_json(
            base,
            dict(
                font="Arial",
                background_color="#eceef0",
                primary_color="#b09641",
                link_color="#7b2424",
            ),
        )
        assert response.status_code == 200
        assert response.json["message"] == "Einstellungen erfolgreich aktualisiert"

    assert _colors(app, db, admin_unit_id) == ("Arial", "#eceef0", "#b09641", "#7b2424")
    data = utils.get_json_ok(base).json
    assert data["font"] == "Arial"
    assert data["background_color"] == "#eceef0"
    assert data["primary_color"] == "#b09641"
    assert data["link_color"] == "#7b2424"


def test_put_does_not_store_the_defaults(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.put_json(
        BASE_URL.format(admin_unit_id),
        dict(
            font="",
            background_color="#ffffff",
            primary_color="#007bff",
            link_color="#007bff",
        ),
    )

    assert response.status_code == 200
    assert _colors(app, db, admin_unit_id) == ("", None, None, None)


def test_put_empty_body(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    assert utils.put_json(BASE_URL.format(admin_unit_id), dict()).status_code == 200


@pytest.mark.parametrize("field", ["background_color", "primary_color", "link_color"])
@pytest.mark.parametrize("value", ["red", "#fff", "#12345g", "007bff"])
def test_put_rejects_invalid_colors(client, seeder, utils, field, value):
    user_id, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.put_json(BASE_URL.format(admin_unit_id), {field: value})

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"][-1] == field


def test_put_rejects_a_long_font(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.put_json(BASE_URL.format(admin_unit_id), dict(font="x" * 256))

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"][-1] == "font"


def test_put_db_error_is_400(client, seeder, utils, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    utils.mock_db_commit(mocker)

    response = utils.put_json(BASE_URL.format(admin_unit_id), dict(font="Arial"))

    assert response.status_code == 400
