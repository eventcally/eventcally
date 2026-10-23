from project.shared.dateutils import create_berlin_date

LIST_URL = "/bff/manage/organizations/{}/events"
OPTIONS_URL = "/bff/manage/organizations/{}/events/options"
ORGANIZERS_URL = "/bff/manage/organizations/{}/event-organizers"
PLACES_URL = "/bff/manage/organizations/{}/event-places"
FUTURE = create_berlin_date(2030, 10, 3, 10)
PAST = create_berlin_date(2020, 10, 3, 10)


def _list(utils, admin_unit_id, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return utils.get_json(f"{LIST_URL.format(admin_unit_id)}?{query}")


def _names(response):
    assert response.status_code == 200, response.json
    return [i["name"] for i in response.json["items"]]


def _foreign_admin_unit(seeder):
    owner_id = seeder.create_user(email="other@test.de")
    return seeder.create_admin_unit(owner_id, name="Andere Crew")


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)

    for url in (
        LIST_URL,
        OPTIONS_URL,
        ORGANIZERS_URL,
        PLACES_URL,
    ):
        assert utils.get_json(url.format(admin_unit_id)).status_code == 401


def test_non_member_is_denied(client, seeder, utils):
    other_id = _foreign_admin_unit(seeder)
    seeder.create_user(email="member@test.de")
    utils.login(email="member@test.de")

    for url in (LIST_URL, OPTIONS_URL, ORGANIZERS_URL, PLACES_URL):
        assert utils.get_json(url.format(other_id)).status_code in (401, 403, 404)


# list


def test_list_returns_own_events_of_every_public_status(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Public", start=FUTURE)
    seeder.create_event(admin_unit_id, name="Draft", start=FUTURE, draft=True)
    seeder.create_event(admin_unit_id, name="Planned", start=FUTURE, planned=True)
    other_id = _foreign_admin_unit(seeder)
    seeder.create_event(other_id, name="Foreign", start=FUTURE)

    response = _list(utils, admin_unit_id, sort="min_start")

    assert sorted(_names(response)) == ["Draft", "Planned", "Public"]
    assert response.json["total"] == 3
    assert response.json["per_page"] == 50


def test_list_item_fields(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(
        admin_unit_id,
        name="Mein Event",
        start=FUTURE,
        draft=True,
        tags="a,b",
        internal_tags="intern",
    )

    item = _list(utils, admin_unit_id).json["items"][0]

    assert item["id"] == event_id
    assert item["public_status"] == "draft"
    assert item["internal_tags"] == "intern"
    assert item["tags"] == "a,b"
    assert item["start"].startswith("2030-10-03")
    assert item["allday"] is False
    assert item["is_recurring"] is False
    assert item["has_photo"] is False
    assert item["organizer_name"]
    assert item["category_names"]


def test_list_hides_past_events_by_default(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Past", start=PAST)
    seeder.create_event(admin_unit_id, name="Future", start=FUTURE)

    assert _names(_list(utils, admin_unit_id)) == ["Future"]
    assert sorted(_names(_list(utils, admin_unit_id, date_from="2020-01-01"))) == [
        "Future",
        "Past",
    ]
    assert _names(_list(utils, admin_unit_id, date_from="")) == ["Future"]


def test_list_date_range(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Past", start=PAST)
    seeder.create_event(admin_unit_id, name="Future", start=FUTURE)

    response = _list(utils, admin_unit_id, date_from="2020-10-03", date_to="2020-10-03")

    assert _names(response) == ["Past"]


def test_list_keyword_and_tags(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Konzert", start=FUTURE, tags="musik")
    seeder.create_event(
        admin_unit_id, name="Lesung", start=FUTURE, internal_tags="geheim"
    )

    assert _names(_list(utils, admin_unit_id, keyword="Konz")) == ["Konzert"]
    assert _names(_list(utils, admin_unit_id, tag="musik")) == ["Konzert"]
    assert _names(_list(utils, admin_unit_id, internal_tag="geheim")) == ["Lesung"]
    assert _names(_list(utils, admin_unit_id, tag="gibtesnicht")) == []


def test_list_category(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Event", start=FUTURE)
    category_id = seeder.get_event_category_id("Other")

    assert _names(_list(utils, admin_unit_id, category_id=category_id)) == ["Event"]
    assert _names(_list(utils, admin_unit_id, category_id=category_id + 999)) == []


def test_list_status_filters(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Public", start=FUTURE)
    seeder.create_event(admin_unit_id, name="Draft", start=FUTURE, draft=True)

    assert _names(_list(utils, admin_unit_id, public_status=1)) == ["Draft"]
    assert _names(_list(utils, admin_unit_id, public_status=2)) == ["Public"]
    assert _names(_list(utils, admin_unit_id, status=2)) == []
    assert _list(utils, admin_unit_id, status=99).status_code == 422
    assert _list(utils, admin_unit_id, public_status=99).status_code == 422


def test_list_is_recurring(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Single", start=FUTURE)
    seeder.create_event(
        admin_unit_id,
        name="Weekly",
        start=FUTURE,
        recurrence_rule="RRULE:FREQ=WEEKLY;COUNT=3",
    )

    assert _names(_list(utils, admin_unit_id, is_recurring="1")) == ["Weekly"]
    assert _names(_list(utils, admin_unit_id, is_recurring="0")) == ["Single"]
    assert _list(utils, admin_unit_id, is_recurring="2").status_code == 422


def test_list_created_at(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Event", start=FUTURE)

    assert _names(_list(utils, admin_unit_id, created_at_from="2020-10-03")) == [
        "Event"
    ]
    assert (
        _names(
            _list(
                utils,
                admin_unit_id,
                created_at_from="2020-10-03",
                created_at_to="2021-10-03",
            )
        )
        == []
    )


def test_list_postal_code(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Event", start=FUTURE)

    assert _names(_list(utils, admin_unit_id, postal_code="00000,00001")) == []


def test_list_radius(client, seeder, utils):
    from project.infrastructure.models import Location

    _, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_event_place(
        admin_unit_id,
        "Goslar",
        Location(
            street="Markt 7",
            postalCode="38640",
            city="Goslar",
            latitude=51.9077888,
            longitude=10.4333312,
        ),
    )
    seeder.create_event(admin_unit_id, name="Near", start=FUTURE, place_id=place_id)
    near = "51.9077888,10.4333312"

    assert _names(
        _list(utils, admin_unit_id, radius_coordinate=near, radius_distance=500)
    ) == ["Near"]
    assert (
        _names(
            _list(
                utils,
                admin_unit_id,
                radius_coordinate="48.1,11.5",
                radius_distance=500,
            )
        )
        == []
    )
    assert (
        _list(
            utils, admin_unit_id, radius_coordinate=near, radius_distance=1
        ).status_code
        == 422
    )
    assert _list(utils, admin_unit_id, radius_coordinate="x").status_code == 422


def test_list_sort(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Later", start=FUTURE)
    seeder.create_event(
        admin_unit_id, name="Earlier", start=create_berlin_date(2030, 1, 1, 10)
    )

    assert _names(_list(utils, admin_unit_id)) == ["Earlier", "Later"]
    assert _names(_list(utils, admin_unit_id, sort="-created_at")) == [
        "Earlier",
        "Later",
    ]
    assert sorted(_names(_list(utils, admin_unit_id, sort="-last_modified_at"))) == [
        "Earlier",
        "Later",
    ]
    assert _list(utils, admin_unit_id, sort="name").status_code == 422


def test_list_pagination(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    for index in range(51):
        seeder.create_event(admin_unit_id, name=f"Event {index}", start=FUTURE)

    first = _list(utils, admin_unit_id)
    second = _list(utils, admin_unit_id, page=2)

    assert first.json["total"] == 51
    assert first.json["pages"] == 2
    assert len(first.json["items"]) == 50
    assert len(second.json["items"]) == 1


def test_list_invalid_date_is_422(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    assert _list(utils, admin_unit_id, date_from="03.10.2020").status_code == 422


def test_list_echoes_preselected_refs(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Event", start=FUTURE)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    unfiltered = _list(utils, admin_unit_id).json
    filtered = _list(
        utils, admin_unit_id, event_place_id=place_id, organizer_id=organizer_id
    ).json

    assert unfiltered["organizer"] is None
    assert unfiltered["event_place"] is None
    assert filtered["organizer"]["id"] == organizer_id
    assert filtered["event_place"]["id"] == place_id
    assert filtered["event_place"]["name"]
    assert [i["name"] for i in filtered["items"]] == ["Event"]


def test_list_ignores_refs_of_other_organizations(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    other_id = _foreign_admin_unit(seeder)
    foreign_place_id = seeder.upsert_default_event_place(other_id)

    response = _list(utils, admin_unit_id, event_place_id=foreign_place_id).json

    assert response["event_place"] is None


# options


def test_options(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_json_ok(OPTIONS_URL.format(admin_unit_id))
    options = response.json

    assert any(c["name"] for c in options["categories"])
    assert [s["name"] for s in options["statuses"]][0] == "scheduled"
    assert [s["value"] for s in options["public_statuses"]] == [1, 2, 3]
    assert all(s["label"] for s in options["statuses"])
    assert options["distances"]
    assert options["can_write"] is True
    assert options["can_request_reference"] is True
    assert len(options["default_date_from"]) == 10


def test_options_unverified_cannot_request_reference(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(admin_unit_verified=False)

    options = utils.get_json_ok(OPTIONS_URL.format(admin_unit_id)).json

    assert options["can_request_reference"] is False


# lookups


def test_lookups_are_scoped_to_the_organization(client, seeder, utils):
    keyword = ""
    _, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    other_id = _foreign_admin_unit(seeder)
    seeder.upsert_event_organizer(other_id, "Fremder Veranstalter")
    seeder.upsert_event_place(other_id, "Fremder Ort")

    organizers = utils.get_json_ok(
        f"{ORGANIZERS_URL.format(admin_unit_id)}?keyword={keyword}"
    ).json["items"]
    places = utils.get_json_ok(
        f"{PLACES_URL.format(admin_unit_id)}?keyword={keyword}"
    ).json["items"]

    assert organizer_id in [o["id"] for o in organizers]
    assert place_id in [p["id"] for p in places]
    assert "Fremder Veranstalter" not in [o["name"] for o in organizers]
    assert "Fremder Ort" not in [p["name"] for p in places]


def test_lookup_filters_by_keyword(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.upsert_event_organizer(admin_unit_id, "Zebra Crew")
    seeder.upsert_event_place(admin_unit_id, "Zebra Halle")

    organizers = utils.get_json_ok(
        f"{ORGANIZERS_URL.format(admin_unit_id)}?keyword=Zebra"
    ).json["items"]
    places = utils.get_json_ok(
        f"{PLACES_URL.format(admin_unit_id)}?keyword=Zebra"
    ).json["items"]

    assert [o["name"] for o in organizers] == ["Zebra Crew"]
    assert [p["name"] for p in places] == ["Zebra Halle"]
