import pytest

LIST_URL = "/bff/manage/organizations/{}/custom-widgets"
ITEM_URL = "/bff/manage/custom-widgets/{}"
SETTINGS = {"layout": "card", "eventsPerPage": 10, "iFrameMaxHeight": "Infinity"}


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/custom-widgets")


def _body(**values):
    body = dict(widget_type="search", name="Mein Widget", settings=SETTINGS)
    body.update(values)
    return body


def _widget(app, widget_id):
    with app.app_context():
        from project.infrastructure.models import CustomWidget

        widget = CustomWidget.query.get(widget_id)
        return widget and (widget.widget_type, widget.name, widget.settings)


def _foreign_widget(seeder):
    owner_id = seeder.create_user(email="other@test.de")
    other_id = seeder.create_admin_unit(owner_id, name="Andere Crew")
    return other_id, seeder.insert_event_custom_widget(other_id, name="Fremd")


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    for call in (
        lambda: utils.get_json(LIST_URL.format(admin_unit_id)),
        lambda: utils.get_json(ITEM_URL.format(widget_id)),
        lambda: utils.post_json(LIST_URL.format(admin_unit_id), _body()),
        lambda: utils.put_json(ITEM_URL.format(widget_id), _body()),
        lambda: utils.delete(ITEM_URL.format(widget_id)),
    ):
        assert call().status_code == 401


def test_foreign_organization_is_403(client, seeder, utils):
    seeder.setup_base()
    other_id, widget_id = _foreign_widget(seeder)

    assert utils.get_json(LIST_URL.format(other_id)).status_code == 403
    assert utils.get_json(ITEM_URL.format(widget_id)).status_code == 403


def test_foreign_organization_writes_are_403(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    other_id, widget_id = _foreign_widget(seeder)

    assert utils.post_json(LIST_URL.format(other_id), _body()).status_code == 403
    assert utils.put_json(ITEM_URL.format(widget_id), _body()).status_code == 403
    assert utils.delete(ITEM_URL.format(widget_id)).status_code == 403
    assert _widget(app, widget_id)[1] == "Fremd"


def test_writes_require_csrf(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    assert utils.post_json(LIST_URL.format(admin_unit_id), _body()).status_code == 400
    assert utils.put_json(ITEM_URL.format(widget_id), _body()).status_code == 400
    assert utils.delete(ITEM_URL.format(widget_id)).status_code == 400


# list


def test_list(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.insert_event_custom_widget(admin_unit_id, name="Zeta")
    seeder.insert_event_custom_widget(
        admin_unit_id, name="Alpha", widget_type="calendar"
    )

    body = utils.get_json_ok(LIST_URL.format(admin_unit_id)).json

    assert [(i["name"], i["widget_type"]) for i in body["items"]] == [
        ("Alpha", "calendar"),
        ("Zeta", "search"),
    ]
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["pages"] == 1
    assert body["can_write"] is True


def test_list_paging(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    for index in range(3):
        seeder.insert_event_custom_widget(admin_unit_id, name=f"Widget {index}")

    body = utils.get_json_ok(f"{LIST_URL.format(admin_unit_id)}?per_page=2&page=2").json

    assert [i["name"] for i in body["items"]] == ["Widget 2"]
    assert body["total"] == 3
    assert body["pages"] == 2


def test_list_unknown_organization_is_404(client, seeder, utils):
    seeder.setup_base()

    utils.assert_response_notFound(utils.get_json(LIST_URL.format(4711)))


def test_list_invalid_page_is_422(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_json(f"{LIST_URL.format(admin_unit_id)}?page=0")

    utils.assert_response_unprocessable_entity(response)


# get


def test_get(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    widget_id = seeder.insert_event_custom_widget(
        admin_unit_id, widget_type="calendar", name="Kalender", settings=SETTINGS
    )

    body = utils.get_json_ok(ITEM_URL.format(widget_id)).json

    assert body == {
        "id": widget_id,
        "organization_id": admin_unit_id,
        "widget_type": "calendar",
        "name": "Kalender",
        "settings": SETTINGS,
    }


def test_get_unknown_is_404(client, seeder, utils):
    seeder.setup_base()

    utils.assert_response_notFound(utils.get_json(ITEM_URL.format(4711)))


# create


def test_create(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.post_json(
        LIST_URL.format(admin_unit_id), _body(name="  Neues Widget  ")
    )

    utils.assert_response_created(response)
    assert _widget(app, response.json["id"]) == ("search", "Neues Widget", SETTINGS)


@pytest.mark.parametrize(
    "values, field",
    [
        (dict(name="ab"), "name"),
        (dict(name="  a  "), "name"),
        (dict(widget_type="unknown"), "widget_type"),
        (dict(settings="nope"), "settings"),
    ],
)
def test_create_invalid_is_422(client, seeder, utils, values, field):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.post_json(LIST_URL.format(admin_unit_id), _body(**values))

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == [field]


# update


def test_update(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    response = utils.put_json(
        ITEM_URL.format(widget_id),
        _body(widget_type="calendar", name="Kalender", settings={"a": 1}),
    )

    assert response.status_code == 204
    assert _widget(app, widget_id) == ("calendar", "Kalender", {"a": 1})


def test_update_unknown_is_404(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    utils.assert_response_notFound(utils.put_json(ITEM_URL.format(4711), _body()))


# delete


def test_delete(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    response = utils.delete(ITEM_URL.format(widget_id))

    assert response.status_code == 204
    assert _widget(app, widget_id) is None


def test_delete_unknown_is_404(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    utils.assert_response_notFound(utils.delete(ITEM_URL.format(4711)))


def test_list_query_filters_by_name(client, container, seeder):
    from project.application.queries import ListCustomWidgetsQuery
    from project.domain.models.entities.actor import Actor

    user_id, admin_unit_id = seeder.setup_base()
    seeder.insert_event_custom_widget(admin_unit_id, name="Zeta Suche")
    seeder.insert_event_custom_widget(admin_unit_id, name="Alpha")

    page = container.cqrs.query_bus().handle(
        ListCustomWidgetsQuery(
            actor=Actor(user_id=user_id), admin_unit_id=admin_unit_id, name="such"
        )
    )

    assert [w.name for w in page.items] == ["Zeta Suche"]
