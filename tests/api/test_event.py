import base64

from project.models import PublicStatus


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


def test_read_otherDraft(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)


def test_read_myDraft(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert response.json["public_status"] == "draft"


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_event_list")
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == event_id


def test_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    image_id = seeder.upsert_default_image()
    seeder.assign_image_to_event(event_id, image_id)
    seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_event_search")
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == event_id


def test_dates(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    url = utils.get_url("api_v1_event_dates", id=event_id)
    utils.get_ok(url)

    event_id = seeder.create_event(admin_unit_id, draft=True)
    url = utils.get_url("api_v1_event_dates", id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)


def test_dates_myDraft(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_event_dates", id=event_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)


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
    put["public_status"] = "draft"

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
        assert event.public_status == PublicStatus.draft

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


def test_put_durationMoreThanMaxAllowedDuration(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    put = create_put(place_id, organizer_id)
    put["start"] = "2021-02-07T11:00:00.000Z"
    put["end"] = "2021-02-21T11:01:00.000Z"

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


def test_put_referencedEventUpdate_sendsMail(client, seeder, utils, app, mocker):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event_via_api(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_reference(event_id, other_admin_unit_id)

    mail_mock = utils.mock_send_mails(mocker)
    url = utils.get_url("api_v1_event", id=event_id)
    put = create_put(place_id, organizer_id)
    put["name"] = "Changed name"
    response = utils.put_json(url, put)

    utils.assert_response_no_content(response)
    utils.assert_send_mail_called(mail_mock, "other@test.de")


def test_put_referencedEventNonDirtyUpdate_doesNotSendMail(
    client, seeder, utils, app, mocker
):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event_via_api(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_reference(event_id, other_admin_unit_id)

    mail_mock = utils.mock_send_mails(mocker)
    url = utils.get_url("api_v1_event", id=event_id)
    put = create_put(place_id, organizer_id)
    put["name"] = "Name"
    response = utils.put_json(url, put)

    utils.assert_response_no_content(response)
    mail_mock.assert_not_called()


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


def test_patch_referencedEventUpdate_sendsMail(client, seeder, utils, app, mocker):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event_via_api(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_reference(event_id, other_admin_unit_id)

    mail_mock = utils.mock_send_mails(mocker)
    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.patch_json(url, {"name": "Changed name"})

    utils.assert_response_no_content(response)
    utils.assert_send_mail_called(mail_mock, "other@test.de")


def test_patch_photo(client, seeder, utils, app, requests_mock):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)

    requests_mock.get(
        "https://image.com", content=base64.b64decode(seeder.get_default_image_base64())
    )

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.patch_json(
        url,
        {"photo": {"image_url": "https://image.com"}},
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import Event

        event = Event.query.get(event_id)
        assert event.photo is not None
        assert event.photo.encoding_format == "image/png"


def test_patch_photo_copyright(client, db, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    image_id = seeder.upsert_default_image()
    seeder.assign_image_to_event(event_id, image_id)

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.patch_json(
        url,
        {"photo": {"copyright_text": "Heiner"}},
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import Event

        event = Event.query.get(event_id)
        assert event.photo.id == image_id
        assert event.photo.data is not None
        assert event.photo.copyright_text == "Heiner"


def test_patch_photo_delete(client, db, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    image_id = seeder.upsert_default_image()
    seeder.assign_image_to_event(event_id, image_id)

    url = utils.get_url("api_v1_event", id=event_id)
    response = utils.patch_json(
        url,
        {"photo": None},
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import Event, Image

        event = Event.query.get(event_id)
        assert event.photo_id is None

        image = Image.query.get(image_id)
        assert image is None


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


def test_report_mail(client, seeder, utils, app, mocker):
    user_id, admin_unit_id = seeder.setup_base(admin=False, log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_user(email="admin@test.de", admin=True)

    mail_mock = utils.mock_send_mails(mocker)
    url = utils.get_url("api_v1_event_reports", id=event_id)
    response = utils.post_json(
        url,
        {
            "contact_name": "Firstname Lastname",
            "contact_email": "firstname.lastname@test.de",
            "message": "Diese Veranstaltung wird nicht stattfinden.",
        },
    )

    utils.assert_response_no_content(response)
    utils.assert_send_mail_called(
        mail_mock,
        ["test@test.de", "admin@test.de"],
        [
            "Firstname Lastname",
            "firstname.lastname@test.de",
            "Diese Veranstaltung wird nicht stattfinden.",
        ],
    )
