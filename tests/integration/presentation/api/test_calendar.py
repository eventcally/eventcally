from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def _list_url(utils, admin_unit_id, **kwargs):
    return utils.get_url(
        "api_v1_organization_calendar_list", id=admin_unit_id, **kwargs
    )


def _url(utils, admin_unit_id, calendar_id):
    return utils.get_url(
        "api_v1_organization_calendar", id=admin_unit_id, calendar_id=calendar_id
    )


def _other_organization(seeder: Seeder):
    other_user_id = seeder.create_user("other@test.de")
    return seeder.create_admin_unit(other_user_id, "Other Crew")


def test_list(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    seeder.create_calendar(admin_unit_id, "Sports")
    seeder.create_calendar(admin_unit_id, "Secret", private=True)

    response = utils.get_json_ok(_list_url(utils, admin_unit_id))
    assert [item["name"] for item in response.json["items"]] == ["Secret", "Sports"]

    response = utils.get_json_ok(_list_url(utils, admin_unit_id, name="spo"))
    assert [item["name"] for item in response.json["items"]] == ["Sports"]


def test_list_hides_private_calendars_from_outsiders(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_api_access(admin=False)
    other_admin_unit_id = _other_organization(seeder)
    seeder.create_calendar(other_admin_unit_id, "Public")
    seeder.create_calendar(other_admin_unit_id, "Secret", private=True)

    response = utils.get_json_ok(_list_url(utils, other_admin_unit_id))

    assert [item["name"] for item in response.json["items"]] == ["Public"]


def test_list_unknown_organization(client, seeder: Seeder, utils: UtilActions):
    seeder.setup_api_access()

    utils.assert_response_notFound(utils.get_json(_list_url(utils, 4711)))


def test_post(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()

    response = utils.post_json(
        _list_url(utils, admin_unit_id),
        {"name": "Sports", "description": "Text", "private": True},
    )
    utils.assert_response_created(response)

    with app.app_context():
        from project.infrastructure.models import Calendar

        calendar = db.session.get(Calendar, response.json["id"])
        assert calendar.name == "Sports"
        assert calendar.description == "Text"
        assert calendar.private is True
        assert calendar.admin_unit_id == admin_unit_id


def test_post_duplicate_name(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    seeder.create_calendar(admin_unit_id, "Sports")

    response = utils.post_json(_list_url(utils, admin_unit_id), {"name": "sports"})

    utils.assert_response_bad_request(response)


def test_post_other_organization(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_admin_unit_id = _other_organization(seeder)

    response = utils.post_json(
        _list_url(utils, other_admin_unit_id), {"name": "Sports"}
    )

    utils.assert_response_unauthorized(response)


def test_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    calendar_id = seeder.create_calendar(admin_unit_id, "Sports")

    response = utils.get_json_ok(_url(utils, admin_unit_id, calendar_id))

    assert response.json["id"] == calendar_id
    assert response.json["name"] == "Sports"
    assert response.json["private"] is False
    assert response.json["organization"]["id"] == admin_unit_id


def test_read_anonym(client, app, seeder: Seeder, utils: UtilActions):
    app.config["API_READ_ANONYM"] = True
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    calendar_id = seeder.create_calendar(admin_unit_id)
    private_id = seeder.create_calendar(admin_unit_id, "Secret", private=True)

    utils.get_json_ok(_url(utils, admin_unit_id, calendar_id))
    utils.assert_response_notFound(
        utils.get_json(_url(utils, admin_unit_id, private_id))
    )


def test_read_private_with_and_without_permission(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_api_access(admin=False)
    other_admin_unit_id = _other_organization(seeder)
    own_id = seeder.create_calendar(admin_unit_id, "Own", private=True)
    foreign_id = seeder.create_calendar(other_admin_unit_id, "Foreign", private=True)

    utils.get_json_ok(_url(utils, admin_unit_id, own_id))
    utils.assert_response_notFound(
        utils.get_json(_url(utils, other_admin_unit_id, foreign_id))
    )


def test_read_other_organization(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_admin_unit_id = _other_organization(seeder)
    calendar_id = seeder.create_calendar(other_admin_unit_id)

    utils.assert_response_notFound(
        utils.get_json(_url(utils, admin_unit_id, calendar_id))
    )
    utils.get_json_ok(_url(utils, other_admin_unit_id, calendar_id))
    utils.assert_response_notFound(utils.get_json(_url(utils, admin_unit_id, 4711)))


def test_put(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    calendar_id = seeder.create_calendar(admin_unit_id)

    response = utils.put_json(
        _url(utils, admin_unit_id, calendar_id),
        {"name": "Neuer Name", "private": True},
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import Calendar

        calendar = db.session.get(Calendar, calendar_id)
        assert calendar.name == "Neuer Name"
        assert calendar.private is True


def test_patch(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    calendar_id = seeder.create_calendar(admin_unit_id, "Sports")

    response = utils.patch_json(
        _url(utils, admin_unit_id, calendar_id), {"description": "Text"}
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import Calendar

        calendar = db.session.get(Calendar, calendar_id)
        assert calendar.name == "Sports"
        assert calendar.description == "Text"


def test_delete(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    calendar_id = seeder.create_calendar(admin_unit_id)

    response = utils.delete(_url(utils, admin_unit_id, calendar_id))
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import Calendar

        assert db.session.get(Calendar, calendar_id) is None


def test_write_other_organization(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_admin_unit_id = _other_organization(seeder)
    calendar_id = seeder.create_calendar(other_admin_unit_id)

    # The calendar belongs to another organization than the path names: 404.
    url = _url(utils, admin_unit_id, calendar_id)
    utils.assert_response_notFound(utils.put_json(url, {"name": "Neu"}))
    utils.assert_response_notFound(utils.patch_json(url, {"name": "Neu"}))
    utils.assert_response_notFound(utils.delete(url))

    # An outsider of the organization named in the path: 401.
    url = _url(utils, other_admin_unit_id, calendar_id)
    utils.assert_response_unauthorized(utils.put_json(url, {"name": "Neu"}))
    utils.assert_response_unauthorized(utils.delete(url))

    with app.app_context():
        from project.infrastructure.models import Calendar

        assert db.session.get(Calendar, calendar_id) is not None
