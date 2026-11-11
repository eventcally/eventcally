def _url(calendar_id):
    return f"/bff/public/calendars/{calendar_id}"


def test_get_calendar_anonymous(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    calendar_id = seeder.create_calendar(admin_unit_id, "Stadtfeste")

    body = utils.get_json_ok(_url(calendar_id)).json

    assert body["id"] == calendar_id
    assert body["name"] == "Stadtfeste"
    assert body["private"] is False
    assert body["organization"] == {"id": admin_unit_id, "name": "Meine Crew"}
    assert body["ical_url"].endswith(f"/calendars/{calendar_id}/ical")
    assert body["manage_url"] is None


def test_get_calendar_gives_members_the_manage_link(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    calendar_id = seeder.create_calendar(admin_unit_id)

    body = utils.get_json_ok(_url(calendar_id)).json

    assert body["manage_url"] == (
        f"/manage/admin_unit/{admin_unit_id}/calendar/{calendar_id}/update"
    )


def test_get_private_calendar(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    calendar_id = seeder.create_calendar(admin_unit_id, private=True)

    assert utils.get_json_ok(_url(calendar_id)).json["private"] is True

    utils.logout()
    assert utils.get_json(_url(calendar_id)).status_code == 404


def test_get_unknown_calendar(client, utils):
    assert utils.get_json(_url(4711)).status_code == 404


def test_lookup_calendars(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    sports = seeder.create_calendar(admin_unit_id, "Sport")
    seeder.create_calendar(admin_unit_id, "Geheim", private=True)

    body = utils.get_json_ok("/bff/public/calendars?keyword=crew&per_page=5").json

    assert body == {
        "items": [
            {
                "id": sports,
                "name": "Sport",
                "organization": {"id": admin_unit_id, "name": "Meine Crew"},
            }
        ]
    }


def test_get_calendar_carries_the_calendar_organization(client, seeder, utils):
    _, owner_admin_unit_id = seeder.setup_base(log_in=False)
    calendar_id = seeder.create_calendar(owner_admin_unit_id, "Stadtfeste")

    assert utils.get_json_ok(_url(calendar_id)).json["calendar_organization"] is None

    _, admin_unit_id = seeder.setup_base(email="member@test.de", name="Andere Crew")
    seeder.create_calendar(admin_unit_id, "Eigener")
    utils.get_ok("/organizations")

    assert utils.get_json_ok(_url(calendar_id)).json["calendar_organization"] == {
        "id": admin_unit_id,
        "name": "Andere Crew",
    }
