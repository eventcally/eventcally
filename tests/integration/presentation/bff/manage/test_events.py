import pytest

from project.shared.dateutils import create_berlin_date

LIST_URL = "/bff/manage/organizations/{}/events"
OPTIONS_URL = "/bff/manage/organizations/{}/events/options"
ORGANIZERS_URL = "/bff/manage/organizations/{}/event-organizers"
PLACES_URL = "/bff/manage/organizations/{}/event-places"
DATES_URL = (
    "/bff/manage/organizations/{}/event-dates?date_from=2030-10-01&date_to=2030-10-31"
)
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
        DATES_URL,
    ):
        assert utils.get_json(url.format(admin_unit_id)).status_code == 401


def test_non_member_is_denied(client, seeder, utils):
    other_id = _foreign_admin_unit(seeder)
    seeder.create_user(email="member@test.de")
    utils.login(email="member@test.de")

    for url in (LIST_URL, OPTIONS_URL, ORGANIZERS_URL, PLACES_URL, DATES_URL):
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


# event dates


def _dates(
    utils, admin_unit_id, date_from="2030-10-01", date_to="2030-10-31", **params
):
    url = (
        f"/bff/manage/organizations/{admin_unit_id}/event-dates"
        f"?date_from={date_from}&date_to={date_to}"
    )
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return utils.get_json(f"{url}&{query}" if query else url)


def _date_names(response):
    assert response.status_code == 200, response.json
    return [i["event"]["name"] for i in response.json["items"]]


def test_dates_returns_own_dates_of_every_public_status(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(
        admin_unit_id, name="Late", start=create_berlin_date(2030, 10, 20, 10)
    )
    seeder.create_event(admin_unit_id, name="Draft", start=FUTURE, draft=True)
    seeder.create_event(
        admin_unit_id,
        name="Planned",
        start=create_berlin_date(2030, 10, 10, 10),
        planned=True,
    )
    seeder.create_event(
        admin_unit_id, name="Outside", start=create_berlin_date(2030, 11, 5, 10)
    )
    other_id = _foreign_admin_unit(seeder)
    seeder.create_event(other_id, name="Foreign", start=FUTURE)

    response = _dates(utils, admin_unit_id)

    assert _date_names(response) == ["Draft", "Planned", "Late"]
    assert response.json["truncated"] is False


def test_dates_item(client, seeder, utils):
    from project.infrastructure.models import Location

    _, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_event_place(
        admin_unit_id, "Rathaus", location=Location(postalCode="38640", city="Goslar")
    )
    seeder.create_event(
        admin_unit_id,
        name="Weekly",
        start=FUTURE,
        place_id=place_id,
        recurrence_rule="RRULE:FREQ=WEEKLY;COUNT=3",
    )

    response = _dates(utils, admin_unit_id)

    assert _date_names(response) == ["Weekly", "Weekly", "Weekly"]
    item = response.json["items"][0]
    assert item["allday"] is False
    assert item["start"] == "2030-10-03T08:00:00Z"
    assert item["event"]["is_recurring"] is True
    assert item["event"]["status"] == "scheduled"
    assert item["event"]["public_status"] == "published"
    assert item["event"]["organizer_name"]
    assert item["event"]["place_label"] == "Rathaus 38640 Goslar"


def test_dates_in_the_past(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, name="Past", start=PAST)

    response = _dates(
        utils, admin_unit_id, date_from="2020-10-01", date_to="2020-10-31"
    )

    assert _date_names(response) == ["Past"]


def test_dates_overlapping_the_range_start(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(
        admin_unit_id,
        name="Festival",
        start=create_berlin_date(2030, 9, 28, 10),
        end=create_berlin_date(2030, 10, 2, 18),
    )

    assert _date_names(_dates(utils, admin_unit_id)) == ["Festival"]


def test_dates_apply_the_list_filters(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(
        admin_unit_id, name="Lesung", start=FUTURE, internal_tags="geheim"
    )
    seeder.create_event(admin_unit_id, name="Entwurf", start=FUTURE, draft=True)
    seeder.create_event(
        admin_unit_id,
        name="Weekly",
        start=FUTURE,
        recurrence_rule="RRULE:FREQ=WEEKLY;COUNT=2",
    )

    assert _date_names(_dates(utils, admin_unit_id, keyword="Les")) == ["Lesung"]
    assert _date_names(_dates(utils, admin_unit_id, internal_tag="geheim")) == [
        "Lesung"
    ]
    assert _date_names(_dates(utils, admin_unit_id, public_status=1)) == ["Entwurf"]
    assert sorted(_date_names(_dates(utils, admin_unit_id, is_recurring="0"))) == [
        "Entwurf",
        "Lesung",
    ]


def test_dates_ignore_the_list_sort(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(
        admin_unit_id, name="Second", start=create_berlin_date(2030, 10, 20, 10)
    )
    seeder.create_event(admin_unit_id, name="First", start=FUTURE)

    response = _dates(utils, admin_unit_id, sort="-created_at")

    assert _date_names(response) == ["First", "Second"]


def test_dates_truncated(client, seeder, utils, monkeypatch):
    from project.presentation.bff.manage import event_dates, events

    monkeypatch.setattr(events, "MAX_DATES", 2)
    monkeypatch.setattr(event_dates, "PAGE_SIZE", 1)
    _, admin_unit_id = seeder.setup_base()

    for day in (3, 4, 5):
        seeder.create_event(
            admin_unit_id, name=f"E{day}", start=create_berlin_date(2030, 10, day, 10)
        )

    response = _dates(utils, admin_unit_id)

    assert _date_names(response) == ["E3", "E4"]
    assert response.json["truncated"] is True


@pytest.mark.parametrize(
    "params",
    [
        dict(date_to="2030-10-31"),
        dict(date_from="2030-10-01"),
        dict(date_from="2030-10-31", date_to="2030-10-01"),
        dict(date_from="2030-10-01", date_to="2031-01-30"),
        dict(date_from="2030-10-01", date_to="2030-10-31", status=99),
    ],
)
def test_dates_invalid_params_are_422(client, seeder, utils, params):
    _, admin_unit_id = seeder.setup_base()
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"/bff/manage/organizations/{admin_unit_id}/event-dates?{query}"

    assert utils.get_json(url).status_code == 422


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


# delete


def _delete_form_url(admin_unit_id, event_id):
    return f"{LIST_URL.format(admin_unit_id)}/{event_id}/delete-form"


def _delete_url(admin_unit_id, event_id):
    return f"{LIST_URL.format(admin_unit_id)}/{event_id}/delete"


def _event_exists(app, event_id):
    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import Event

        return db.session.get(Event, event_id) is not None


@pytest.fixture
def csrf(client, utils, seeder):
    """Any Vue 3 shell carries the CSRF token for the writes."""
    _, admin_unit_id = seeder.setup_base()
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/events")
    return admin_unit_id


def test_delete_form(client, seeder, utils, csrf):
    event_id = seeder.create_event(csrf, name="Jam Session", start=FUTURE)

    response = utils.get_json(_delete_form_url(csrf, event_id))

    assert response.status_code == 200
    assert response.json == {
        "id": event_id,
        "name": "Jam Session",
        "has_multiple_dates": False,
    }


def test_delete_form_warns_about_several_dates(client, seeder, utils, csrf):
    event_id = seeder.create_event(
        csrf, start=FUTURE, recurrence_rule="RRULE:FREQ=DAILY;COUNT=3"
    )

    response = utils.get_json(_delete_form_url(csrf, event_id))

    assert response.json["has_multiple_dates"] is True


def test_delete_flashes_and_answers_the_list(client, app, seeder, utils, csrf):
    event_id = seeder.create_event(csrf)

    response = utils.post_json(_delete_url(csrf, event_id), {})

    assert response.status_code == 200
    assert response.json == {
        "message": "Veranstaltung erfolgreich gelöscht",
        "redirect_url": f"/manage/admin_unit/{csrf}/events",
    }
    assert not _event_exists(app, event_id)

    with client.session_transaction() as session:
        flashes = [(c, str(m)) for c, m in session["_flashes"]]

    assert flashes == [("success", "Veranstaltung erfolgreich gelöscht")]


def test_inline_delete_does_not_flash(client, app, seeder, utils, csrf):
    event_id = seeder.create_event(csrf)

    response = utils.post_json(_delete_url(csrf, event_id), {"inline": True})

    assert response.status_code == 200
    assert response.json["message"] == "Veranstaltung erfolgreich gelöscht"
    assert not _event_exists(app, event_id)

    with client.session_transaction() as session:
        assert "_flashes" not in session


def test_delete_db_error_is_400(client, app, seeder, utils, mocker, csrf):
    event_id = seeder.create_event(csrf)
    utils.mock_db_commit(mocker)

    response = utils.post_json(_delete_url(csrf, event_id), {})

    assert response.status_code == 400
    assert response.json["name"] == "InfrastructureError"


def test_delete_of_another_organization_is_404(client, app, seeder, utils, csrf):
    other_id = seeder.create_admin_unit(
        seeder.create_user(email="other@test.de"), name="Andere Crew", verified=True
    )
    # The event of a verified organization is readable, but not the user's own.
    other_event_id = seeder.create_event(other_id, name="Foreign")

    for call in (
        lambda: utils.get_json(_delete_form_url(csrf, other_event_id)),
        lambda: utils.post_json(_delete_url(csrf, other_event_id), {}),
        lambda: utils.get_json(_delete_form_url(csrf, 4711)),
    ):
        assert call().status_code == 404

    # A draft of another organization is not readable at all.
    draft_id = seeder.create_event(other_id, name="Draft", draft=True)
    assert utils.get_json(_delete_form_url(csrf, draft_id)).status_code == 404
    assert utils.post_json(_delete_url(csrf, draft_id), {}).status_code == 404

    assert _event_exists(app, other_event_id)
    assert utils.get_json(_delete_form_url(other_id, other_event_id)).status_code == 403
    assert utils.post_json(_delete_url(other_id, other_event_id), {}).status_code == 403


def test_delete_access(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    event_id = seeder.create_event(admin_unit_id)

    assert utils.get_json(_delete_form_url(admin_unit_id, event_id)).status_code == 401
    assert utils.post_json(_delete_url(admin_unit_id, event_id), {}).status_code == 401

    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    utils.get_ok("/organizations")

    assert utils.get_json(_delete_form_url(admin_unit_id, event_id)).status_code == 403
    assert utils.post_json(_delete_url(admin_unit_id, event_id), {}).status_code == 403
