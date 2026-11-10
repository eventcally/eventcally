BASE = "/bff/manage/organizations/{}/calendars"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/calendars")


def _flashes(client):
    with client.session_transaction() as session:
        return [
            (category, str(message))
            for category, message in session.get("_flashes", [])
        ]


def _other_organization(seeder):
    owner_id = seeder.create_user(email="other@test.de")
    return seeder.create_admin_unit(owner_id, name="Andere Crew")


def _setup(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    return admin_unit_id


def _names(calendar_id, app):
    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import Calendar

        calendar = db.session.get(Calendar, calendar_id)
        return calendar and (calendar.name, calendar.description, calendar.private)


# access


def test_anonymous_is_401(client, seeder, utils):
    admin_unit_id = seeder.create_admin_unit(seeder.create_user())
    base = BASE.format(admin_unit_id)

    for call in (
        lambda: utils.get_json(f"{base}/list"),
        lambda: utils.get_json(f"{base}/create-form"),
        lambda: utils.get_json(f"{base}/choices"),
        lambda: utils.get_json(f"{base}/1"),
        lambda: utils.post_json(base, {"name": "x"}),
    ):
        assert call().status_code == 401


def test_member_without_rights_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    calendar_id = seeder.create_calendar(admin_unit_id)
    utils.get_ok("/organizations")
    base = BASE.format(admin_unit_id)

    for url in (
        f"{base}/list",
        f"{base}/create-form",
        f"{base}/choices",
        f"{base}/name-availability?name=x",
        f"{base}/{calendar_id}",
    ):
        assert utils.get_json(url).status_code == 403
    assert utils.post_json(base, {"name": "x"}).status_code == 403
    assert utils.put_json(f"{base}/{calendar_id}", {"name": "x"}).status_code == 403


def test_calendar_of_another_organization_is_404(client, app, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    other_id = _other_organization(seeder)
    foreign_id = seeder.create_calendar(other_id, "Fremd")
    url = f"{BASE.format(admin_unit_id)}/{foreign_id}"

    assert utils.get_json(url).status_code == 404
    assert utils.put_json(url, {"name": "Neu"}).status_code == 404
    assert utils.post_json(f"{url}/delete", {"name": "Fremd"}).status_code == 404
    assert utils.get_json(f"{BASE.format(admin_unit_id)}/4711").status_code == 404
    assert _names(foreign_id, app) == ("Fremd", None, False)


# forms and list


def test_forms(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    calendar_id = seeder.create_calendar(admin_unit_id, "Sport", private=True)
    base = BASE.format(admin_unit_id)

    create = utils.get_json_ok(f"{base}/create-form").json
    assert create["id"] is None and create["name"] == "" and create["private"] is False

    form = utils.get_json_ok(f"{base}/{calendar_id}").json
    assert (form["id"], form["name"], form["private"]) == (calendar_id, "Sport", True)


def test_list_and_choices(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    seeder.create_calendar(admin_unit_id, "Sport")
    seeder.create_calendar(admin_unit_id, "Geheim", private=True)
    _other_organization(seeder)
    base = BASE.format(admin_unit_id)

    page = utils.get_json_ok(f"{base}/list").json

    assert [(i["name"], i["private"]) for i in page["items"]] == [
        ("Geheim", True),
        ("Sport", False),
    ]
    assert page["can_write"] is True
    public = {i["name"]: i["public_url"] for i in page["items"]}
    assert public["Geheim"] is None and public["Sport"].startswith("/calendars/")
    assert [
        i["name"] for i in utils.get_json_ok(f"{base}/list?keyword=sp").json["items"]
    ] == ["Sport"]
    assert utils.get_json(f"{base}/list?page=9").status_code == 404

    choices = utils.get_json_ok(f"{base}/choices").json["items"]
    assert [(c["name"], c["private"]) for c in choices] == [
        ("Geheim", True),
        ("Sport", False),
    ]


def test_name_availability(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    calendar_id = seeder.create_calendar(admin_unit_id, "Sport")
    url = f"{BASE.format(admin_unit_id)}/name-availability"

    assert utils.get_json_ok(f"{url}?name=sport").json["name_taken"] is True
    assert utils.get_json_ok(f"{url}?name=Neu").json["name_taken"] is False
    assert (
        utils.get_json_ok(f"{url}?name=sport&exclude_id={calendar_id}").json[
            "name_taken"
        ]
        is False
    )
    assert utils.get_json_ok(url).json["name_taken"] is None


# writes


def test_create_update_and_delete(client, app, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    base = BASE.format(admin_unit_id)

    response = utils.post_json(
        base, {"name": " Sport ", "description": "Text", "private": True}
    )
    assert response.status_code == 201
    calendar_id = response.json["id"]
    assert (
        response.json["redirect_url"] == f"/manage/admin_unit/{admin_unit_id}/calendars"
    )
    assert _names(calendar_id, app) == ("Sport", "Text", True)
    assert _flashes(client)[-1][0] == "success"

    response = utils.put_json(
        f"{base}/{calendar_id}", {"name": "Sport", "description": "", "private": False}
    )
    assert response.status_code == 200
    assert _names(calendar_id, app) == ("Sport", None, False)

    response = utils.post_json(f"{base}/{calendar_id}/delete", {"name": "sport"})
    assert response.status_code == 200
    assert _names(calendar_id, app) is None


def test_create_inline_does_not_flash(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)

    utils.post_json(BASE.format(admin_unit_id), {"name": "Sport", "inline": True})

    assert _flashes(client) == []


def test_duplicate_name_is_a_field_error(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    base = BASE.format(admin_unit_id)
    other_id = seeder.create_calendar(admin_unit_id, "Zwei")
    seeder.create_calendar(admin_unit_id, "Sport")

    response = utils.post_json(base, {"name": "sport"})
    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]
    assert utils.put_json(f"{base}/{other_id}", {"name": "SPORT"}).status_code == 422


def test_delete_needs_the_name(client, app, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    calendar_id = seeder.create_calendar(admin_unit_id, "Sport")

    response = utils.post_json(
        f"{BASE.format(admin_unit_id)}/{calendar_id}/delete", {"name": "falsch"}
    )

    assert response.status_code == 422
    assert _names(calendar_id, app) is not None


# calendars of an event


def test_event_calendars(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    event_id = seeder.create_event(admin_unit_id)
    first = seeder.create_calendar(admin_unit_id, "Erster")
    second = seeder.create_calendar(admin_unit_id, "Zweiter")
    seeder.create_calendar_entry(first, event_id)
    url = f"/bff/manage/organizations/{admin_unit_id}/events/{event_id}/calendars"

    body = utils.get_json_ok(url).json
    assert [c["id"] for c in body["choices"]] == [first, second]
    assert body["selected_ids"] == [first]

    response = utils.put_json(url, {"calendar_ids": [second]})
    assert response.status_code == 200
    assert utils.get_json_ok(url).json["selected_ids"] == [second]


def test_event_calendars_reject_foreign_calendars_and_events(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    other_id = _other_organization(seeder)
    event_id = seeder.create_event(admin_unit_id)
    foreign_calendar = seeder.create_calendar(other_id, "Fremd")
    foreign_draft = seeder.create_event(other_id, name="Fremd", draft=True)
    own_url = f"/bff/manage/organizations/{admin_unit_id}/events/{event_id}/calendars"

    assert (
        utils.put_json(own_url, {"calendar_ids": [foreign_calendar]}).status_code == 422
    )
    url = f"/bff/manage/organizations/{admin_unit_id}/events/{foreign_draft}/calendars"
    assert utils.get_json(url).status_code == 404
    assert utils.put_json(url, {"calendar_ids": []}).status_code == 404


def test_choices_collect_every_page(client, seeder, utils):
    admin_unit_id = _setup(seeder, utils)
    for number in range(101):
        seeder.create_calendar(admin_unit_id, f"Kalender {number:03d}")

    choices = utils.get_json_ok(f"{BASE.format(admin_unit_id)}/choices").json["items"]

    assert len(choices) == 101
    assert choices[-1]["name"] == "Kalender 100"
