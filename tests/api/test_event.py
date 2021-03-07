def test_read(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import Event, EventStatus
        from project.services.event import update_event

        event = Event.query.get(event_id)
        event.status = EventStatus.scheduled

        update_event(event)
        db.session.commit()

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.get_ok(url)
    assert response.json["status"] == "scheduled"


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event_list")
    utils.get_ok(url)


def test_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event_search")
    utils.get_ok(url)


def test_dates(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event_dates", id=event_id)
    utils.get_ok(url)


def create_put(
    place_id, organizer_id, name="Neuer Name", start="2021-02-07T11:00:00.000Z"
):
    return {
        "name": name,
        "start": start,
        "place": {"id": place_id},
        "organizer": {"id": organizer_id},
    }


def test_put(client, seeder, utils, app, mocker):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    utils.mock_now(mocker, 2020, 1, 1)

    put = create_put(place_id, organizer_id)
    put["rating"] = 10
    put["description"] = "Neue Beschreibung"
    put["external_link"] = "http://www.google.de"
    put["ticket_link"] = "http://www.yahoo.de"
    put["tags"] = "Freizeit, Klönen"
    put["kid_friendly"] = True
    put["accessible_for_free"] = True
    put["age_from"] = 9
    put["age_to"] = 99
    put["target_group_origin"] = "tourist"
    put["attendance_mode"] = "online"
    put["status"] = "movedOnline"
    put["previous_start_date"] = "2021-02-07T10:00:00+01:00"
    put["registration_required"] = True
    put["booked_up"] = True
    put["expected_participants"] = 500
    put["price_info"] = "Erwachsene 5€, Kinder 2€."
    put["recurrence_rule"] = "RRULE:FREQ=DAILY;COUNT=7"

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.dateutils import create_berlin_date
        from project.models import (
            Event,
            EventAttendanceMode,
            EventStatus,
            EventTargetGroupOrigin,
        )

        event = Event.query.get(event_id)
        assert event.name == "Neuer Name"
        assert event.event_place_id == place_id
        assert event.organizer_id == organizer_id
        assert event.rating == put["rating"]
        assert event.description == put["description"]
        assert event.external_link == put["external_link"]
        assert event.ticket_link == put["ticket_link"]
        assert event.tags == put["tags"]
        assert event.kid_friendly == put["kid_friendly"]
        assert event.accessible_for_free == put["accessible_for_free"]
        assert event.age_from == put["age_from"]
        assert event.age_to == put["age_to"]
        assert event.target_group_origin == EventTargetGroupOrigin.tourist
        assert event.attendance_mode == EventAttendanceMode.online
        assert event.status == EventStatus.movedOnline
        assert event.previous_start_date == create_berlin_date(2021, 2, 7, 10, 0)
        assert event.registration_required == put["registration_required"]
        assert event.booked_up == put["booked_up"]
        assert event.expected_participants == put["expected_participants"]
        assert event.price_info == put["price_info"]
        assert event.recurrence_rule == put["recurrence_rule"]

        len_dates = len(event.dates)
        assert len_dates == 7


def test_put_invalidRecurrenceRule(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id)
    put["recurrence_rule"] = "RRULE:FREQ=SCHMAILY;COUNT=7"

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_unprocessable_entity(response)


def test_put_missingName(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id)
    del put["name"]

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_unprocessable_entity(response)


def test_put_missingPlace(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id)
    del put["place"]

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_unprocessable_entity(response)


def test_put_placeFromAnotherAdminUnit(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew")
    place_id = seeder.upsert_default_event_place(other_admin_unit_id)

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, create_put(place_id, organizer_id))
    utils.assert_response_bad_request(response)
    utils.assert_response_api_error(response, "Check Violation")


def test_put_missingOrganizer(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id)
    del put["organizer"]

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_unprocessable_entity(response)


def test_put_organizerFromAnotherAdminUnit(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew")
    organizer_id = seeder.upsert_default_event_organizer(other_admin_unit_id)

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, create_put(place_id, organizer_id))
    utils.assert_response_bad_request(response)
    utils.assert_response_api_error(response, "Check Violation")


def test_put_invalidDateFormat(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id, start="07.02.2021T11:00:00.000Z")

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_unprocessable_entity(response)


def test_put_startAfterEnd(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id)
    put["start"] = "2021-02-07T11:00:00.000Z"
    put["end"] = "2021-02-07T10:59:00.000Z"

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_bad_request(response)


def test_put_durationMoreThan24Hours(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id)
    put["start"] = "2021-02-07T11:00:00.000Z"
    put["end"] = "2021-02-08T11:01:00.000Z"

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_bad_request(response)


def test_put_categories(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    category_id = seeder.get_event_category_id("Art")

    put = create_put(place_id, organizer_id)
    put["categories"] = [{"id": category_id}]

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import Event

        event = Event.query.get(event_id)
        assert event.category.name == "Art"


def test_put_dateWithTimezone(client, seeder, utils, app):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id, start="2030-12-31T14:30:00+01:00")

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import Event

        expected = create_berlin_date(2030, 12, 31, 14, 30)

        event = Event.query.get(event_id)
        assert event.start == expected


def test_put_dateWithoutTimezone(client, seeder, utils, app):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id, start="2030-12-31T14:30:00")

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.put_json(url, put)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import Event

        expected = create_berlin_date(2030, 12, 31, 14, 30)

        event = Event.query.get(event_id)
        assert event.start == expected


def test_patch(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.patch_json(url, {"description": "Neu"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import Event

        event = Event.query.get(event_id)
        assert event.name == "Name"
        assert event.description == "Neu"


def test_patch_startAfterEnd(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.patch_json(url, {"start": "2021-02-07T11:00:00.000Z"})
    utils.assert_response_no_content(response)

    response = utils.patch_json(url, {"end": "2021-02-07T10:59:00.000Z"})
    utils.assert_response_bad_request(response)


def test_delete(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import Event

        event = Event.query.get(event_id)
        assert event is None
