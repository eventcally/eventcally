from project.shared.dateutils import create_berlin_date

OPTIONS_URL = "/bff/public/event-dates/options"
SEARCH_URL = "/bff/public/event-dates"
START = create_berlin_date(2030, 10, 3, 10)


def _url(base=SEARCH_URL, **params):
    query = dict(date_from="2030-10-01") if base == SEARCH_URL else {}
    query.update(params)
    return base + "?" + "&".join(f"{k}={v}" for k, v in query.items())


def _names(response):
    return sorted(i["event"]["name"] for i in response.json["items"])


def _other_org(seeder, name="Andere Crew"):
    owner_id = seeder.create_user(email="other@test.de")
    return seeder.create_admin_unit(owner_id, name=name, verified=True)


# options


def test_options_anonymous(client, seeder, utils):
    owner_id = seeder.create_user()
    seeder.create_admin_unit(owner_id, verified=True)

    body = utils.get_json_ok(OPTIONS_URL).json

    names = [c["name"] for c in body["categories"]]
    assert names == sorted(names)
    assert body["default_date_from"]
    assert body["referencing_organization"] is None
    assert body["organization"] is None
    assert body["organizer"] is None
    assert [d["value"] for d in body["distances"]][0] == 500
    assert [s["value"] for s in body["sorts"]] == ["start", "-created_at"]


def test_options_member_has_referencing_organization(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    body = utils.get_json_ok(OPTIONS_URL).json

    assert body["referencing_organization"] == {
        "id": admin_unit_id,
        "name": "Meine Crew",
    }


def test_options_resolves_organization_and_organizer(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    body = utils.get_json_ok(_url(OPTIONS_URL, admin_unit_id=admin_unit_id)).json
    assert body["organization"] == {"id": admin_unit_id, "name": "Meine Crew"}
    assert body["organizer"] is None

    body = utils.get_json_ok(_url(OPTIONS_URL, organizer_id=organizer_id)).json
    assert body["organization"] == {"id": admin_unit_id, "name": "Meine Crew"}
    assert body["organizer"]["id"] == organizer_id


def test_options_unknown_ids_are_none(client, seeder, utils):
    body = utils.get_json_ok(
        _url(OPTIONS_URL, admin_unit_id=4711, organizer_id=4712)
    ).json

    assert body["organization"] is None
    assert body["organizer"] is None


# search


def test_search_anonymous(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id, name="Published", start=START)
    seeder.create_event(admin_unit_id, name="Draft", start=START, draft=True)
    seeder.create_event(admin_unit_id, name="Planned", start=START, planned=True)

    response = utils.get_json_ok(_url())

    assert _names(response) == ["Published"]
    item = response.json["items"][0]
    assert item["event"]["organization"] == {"id": admin_unit_id, "name": "Meine Crew"}
    assert item["event"]["description_preview"] == "Beschreibung"
    assert item["event"]["reference"] is None
    assert item["event"]["place"]["latitude"] is None
    assert response.json["per_page"] == 50


def test_search_default_date_is_today(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(
        admin_unit_id, name="Past", start=create_berlin_date(2001, 1, 1)
    )
    seeder.create_event(admin_unit_id, name="Future", start=START)

    assert _names(utils.get_json_ok(SEARCH_URL)) == ["Future"]


def test_search_filters(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    other_id = _other_org(seeder)
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Veranstalter")
    seeder.create_event(admin_unit_id, name="Konzert", start=START, tags="musik,live")
    seeder.create_event(admin_unit_id, name="Lesung", start=START)
    seeder.create_event(other_id, name="Fremd", start=START)
    seeder.create_event(
        admin_unit_id, name="Spaet", start=create_berlin_date(2030, 11, 20, 10)
    )
    seeder.create_event(
        admin_unit_id,
        name="Serie",
        start=START,
        recurrence_rule="RRULE:FREQ=DAILY;COUNT=2",
    )

    assert _names(utils.get_json_ok(_url(keyword="Konz"))) == ["Konzert"]
    assert _names(utils.get_json_ok(_url(tag="live"))) == ["Konzert"]
    assert _names(utils.get_json_ok(_url(admin_unit_id=other_id))) == ["Fremd"]
    assert "Fremd" not in _names(utils.get_json_ok(_url(admin_unit_id=admin_unit_id)))
    assert _names(utils.get_json_ok(_url(date_to="2030-10-03"))) == [
        "Fremd",
        "Konzert",
        "Lesung",
        "Serie",
    ]
    assert _names(
        utils.get_json_ok(_url(exclude_recurring="true", date_to="2030-10-03"))
    ) == [
        "Fremd",
        "Konzert",
        "Lesung",
    ]
    assert utils.get_json_ok(_url(organizer_id=organizer_id)).json["total"] == 0


def test_search_category_zero_means_any(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id, name="Konzert", start=START)

    assert _names(utils.get_json_ok(_url(category_id=0))) == ["Konzert"]
    assert _names(utils.get_json_ok(_url(category_id=4711))) == []


def test_search_created_at_range_and_sort(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id, name="Erst", start=START)
    seeder.create_event(
        admin_unit_id, name="Zweit", start=create_berlin_date(2030, 10, 2)
    )

    names = [
        i["event"]["name"]
        for i in utils.get_json_ok(_url(sort="-created_at")).json["items"]
    ]
    assert names == ["Zweit", "Erst"]
    assert _names(utils.get_json_ok(_url(created_at_from="2001-01-01"))) == [
        "Erst",
        "Zweit",
    ]
    assert _names(utils.get_json_ok(_url(created_at_to="2001-01-01"))) == []


def test_search_coordinate_and_distance(client, app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)

    with app.app_context():
        from project.infrastructure.models import Location

        location = Location(
            city="Goslar",
            postalCode="38640",
            latitude="51.9077888",
            longitude="10.4333312",
        )
        place_id = seeder.upsert_event_place(admin_unit_id, "Halle", location)

    seeder.create_event(admin_unit_id, name="Nah", start=START, place_id=place_id)
    seeder.create_event(admin_unit_id, name="Ohne", start=START)

    response = utils.get_json_ok(_url(coordinate="51.9077888,10.4333312", distance=500))

    assert _names(response) == ["Nah"]
    place = response.json["items"][0]["event"]["place"]
    assert place["name"] == "Halle"
    assert abs(place["latitude"] - 51.9077888) < 1e-6
    assert abs(place["longitude"] - 10.4333312) < 1e-6
    assert _names(utils.get_json_ok(_url(coordinate="40.0,10.0", distance=500))) == []
    assert _names(utils.get_json_ok(_url(postal_code="38640"))) == ["Nah"]
    assert _names(utils.get_json_ok(_url(postal_code="99999"))) == []


def test_search_invalid_coordinate_is_422(client, seeder, utils):
    assert utils.get_json(_url(coordinate="abc")).status_code == 422


def test_search_out_of_range_page_is_404(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id, name="Konzert", start=START)

    assert utils.get_json(_url(page=5)).status_code == 404


def test_search_photo(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, name="Konzert", start=START)
    seeder.assign_image_to_event(event_id, seeder.upsert_default_image())

    photo = utils.get_json_ok(_url()).json["items"][0]["event"]["photo"]

    assert "s=200" in photo["url_200"]


# references


def test_search_reference_states_for_member(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    other_id = _other_org(seeder)
    seeder.create_event(admin_unit_id, name="Eigen", start=START)
    seeder.create_event(other_id, name="Frei", start=START)
    referenced_id = seeder.create_event(other_id, name="Referenziert", start=START)
    reference_id = seeder.create_reference(referenced_id, admin_unit_id)

    items = {
        i["event"]["name"]: i["event"]["reference"]
        for i in utils.get_json_ok(_url()).json["items"]
    }

    assert items["Eigen"] == {"state": "own", "reference_id": None}
    assert items["Frei"] == {"state": "none", "reference_id": None}
    assert items["Referenziert"] == {
        "state": "referenced",
        "reference_id": reference_id,
    }


def test_not_referenced_filters_for_member(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    other_id = _other_org(seeder)
    free_id = seeder.create_event(other_id, name="Frei", start=START)
    referenced_id = seeder.create_event(other_id, name="Referenziert", start=START)
    seeder.create_reference(referenced_id, admin_unit_id)

    assert _names(utils.get_json_ok(_url(not_referenced="true"))) == ["Frei"]
    assert free_id


def test_not_referenced_is_ignored_for_anonymous(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id, name="Konzert", start=START)

    assert _names(utils.get_json_ok(_url(not_referenced="true"))) == ["Konzert"]
