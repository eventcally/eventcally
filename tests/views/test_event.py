import pytest
from psycopg2.errors import UniqueViolation

from tests.seeder import Seeder
from tests.utils import UtilActions


@pytest.mark.parametrize(
    "external_link", [None, "https://example.com", "www.example.com"]
)
def test_read(client, seeder: Seeder, utils: UtilActions, external_link):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, external_link=external_link)

    url = utils.get_url("event", event_id=event_id)
    utils.get_ok(url)

    event_id = seeder.create_event(admin_unit_id, draft=True)
    url = utils.get_url("event", event_id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    utils.login()
    utils.get_ok(url)

    _, _, event_id = seeder.create_event_unverified()
    url = utils.get_url("event", event_id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)


def test_read_containsActionLink(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(
        other_user_id, "Other Crew", verified=True
    )
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("event", event_id=event_id)
    response = utils.get_ok(url)

    action_url = utils.get_url("event_actions", event_id=event_id)
    assert action_url in str(response.data)


def test_read_shows_reference_requests(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()

    other_user_id, other_admin_unit_id, event_id, reference_request_id = (
        seeder.create_outgoing_reference_request(admin_unit_id)
    )

    url = utils.get_url("event", event_id=event_id)
    utils.get_ok(url)


def test_read_co_organizers(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    event_id, organizer_a_id, organizer_b_id = seeder.create_event_with_co_organizers(
        admin_unit_id
    )

    url = utils.get_url("event", event_id=event_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "Organizer A")
    utils.assert_response_contains(response, "Organizer B")


@pytest.mark.parametrize("variant", ["normal", "db_error", "two_date_definitions"])
def test_create(client, app, utils: UtilActions, seeder: Seeder, mocker, variant):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    if variant == "db_error":
        utils.mock_db_commit(mocker, UniqueViolation("MockException", "MockException"))

    data = {
        "name": "Name",
        "description": "Beschreibung",
        "date_definitions-0-start": ["2030-12-31", "23:59"],
        "event_place": place_id,
        "organizer": organizer_id,
        "photo-image_base64": seeder.get_default_image_upload_base64(),
        "photo-copyright_text": "EventCally",
    }

    if variant == "two_date_definitions":
        data["date_definitions-1-start"] = ["2030-12-31", "14:00"]

    response = utils.post_form(
        url,
        response,
        data,
    )

    if variant == "db_error":
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "event_actions", event_id=1)

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        assert event is not None

        if variant == "two_date_definitions":
            assert len(event.date_definitions) == 2
        else:
            assert len(event.date_definitions) == 1


def test_create_unauthorized(client, app, utils: UtilActions, seeder: Seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    response = utils.get_endpoint("manage_admin_unit.event_create", id=admin_unit_id)
    utils.assert_response_permission_missing(
        response, "manage_admin_unit", id=admin_unit_id
    )


def test_create_allday(client, app, utils: UtilActions, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "date_definitions-0-start": ["2030-12-31", "00:00"],
            "date_definitions-0-end": ["2030-12-31", "23:59"],
            "date_definitions-0-allday": "y",
            "event_place": place_id,
            "organizer": organizer_id,
            "photo-image_base64": seeder.get_default_image_upload_base64(),
            "photo-copyright_text": "EventCally",
        },
    )

    utils.assert_response_redirect(response, "event_actions", event_id=1)

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        assert event is not None
        assert event.date_definitions[0].allday


def test_create_with_reference_requests(
    client, app, utils: UtilActions, seeder: Seeder
):
    user_id, admin_unit_id = seeder.setup_base()
    eventcally_admin_unit_id = seeder.get_eventcally_admin_unit_id()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(
        other_user_id,
        "Other Crew",
        verified=True,
        incoming_verification_requests_allowed=True,
    )
    seeder.create_admin_unit_relation(
        other_admin_unit_id, admin_unit_id, auto_verify_event_reference_requests=True
    )

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "date_definitions-0-start": ["2030-12-31", "00:00"],
            "date_definitions-0-end": ["2030-12-31", "23:59"],
            "event_place": place_id,
            "organizer": organizer_id,
            "reference_request_admin_unit_id": [
                eventcally_admin_unit_id,
                other_admin_unit_id,
            ],
        },
    )

    utils.assert_response_redirect(response, "event_actions", event_id=1)

    with app.app_context():
        from project.models import (
            Event,
            EventReference,
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        assert event is not None

        reference_request = (
            EventReferenceRequest.query.filter(
                EventReferenceRequest.admin_unit_id == eventcally_admin_unit_id
            )
            .filter(EventReferenceRequest.event_id == event.id)
            .first()
        )
        assert reference_request is not None
        assert (
            reference_request.review_status == EventReferenceRequestReviewStatus.inbox
        )

        reference_request = (
            EventReferenceRequest.query.filter(
                EventReferenceRequest.admin_unit_id == other_admin_unit_id
            )
            .filter(EventReferenceRequest.event_id == event.id)
            .first()
        )
        assert reference_request is not None
        assert (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.verified
        )

        reference = (
            EventReference.query.filter(
                EventReference.admin_unit_id == other_admin_unit_id
            )
            .filter(EventReference.event_id == event.id)
            .first()
        )
        assert reference is not None


def test_create_newPlaceAndOrganizer(
    client, app, utils: UtilActions, seeder: Seeder, mocker
):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "date_definitions-0-start": ["2030-12-31", "23:59"],
            "organizer_choice": 2,
            "new_organizer-name": "Neuer Veranstalter",
            "event_place_choice": 2,
            "new_event_place-name": "Neuer Ort",
        },
    )
    utils.assert_response_redirect(response, "event_actions", event_id=1)

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        assert event is not None


def test_create_missingName(client, app, utils: UtilActions, seeder: Seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {},
    )

    utils.assert_response_error_message(response)


def test_create_missingPlace(client, app, utils: UtilActions, seeder: Seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "date_definitions-0-start": ["2030-12-31", "23:59"],
        },
    )

    utils.assert_response_error_message(response)


def test_create_missingOrganizer(
    client, app, utils: UtilActions, seeder: Seeder, mocker
):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "date_definitions-0-start": ["2030-12-31", "23:59"],
            "event_place": place_id,
        },
    )

    utils.assert_response_error_message(response)


def test_create_invalidOrganizer(
    client, app, utils: UtilActions, seeder: Seeder, mocker
):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "date_definitions-0-start": ["2030-12-31", "23:59"],
            "event_place": place_id,
            "organizer": organizer_id,
            "co_organizers": [organizer_id],
        },
    )

    utils.assert_response_error_message(response)
    utils.assert_response_contains(response, "Ungültiger Mitveranstalter")


def test_create_invalidDateFormat(
    client, app, utils: UtilActions, seeder: Seeder, mocker
):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "date_definitions-0-start": ["2030-12-31", "23:59"],
            "event_place": place_id,
        },
    )

    utils.assert_response_error_message(response)


def test_create_startInvalid(client, app, utils: UtilActions, seeder: Seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "date_definitions-0-start": ["31.12.2030", "23:59"],
            "date_definitions-0-end": ["2030-12-31", "23:58"],
            "event_place": place_id,
        },
    )

    utils.assert_response_error_message(response)


def test_create_startAfterEnd(client, app, utils: UtilActions, seeder: Seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "date_definitions-0-start": ["2030-12-31", "23:59"],
            "date_definitions-0-end": ["2030-12-31", "23:58"],
            "event_place": place_id,
            "organizer": organizer_id,
        },
    )

    utils.assert_response_error_message(
        response,
        "Der Start muss vor dem Ende sein",
    )


def test_create_durationMoreThanMaxAllowedDuration(
    client, app, utils: UtilActions, seeder: Seeder, mocker
):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "date_definitions-0-start": ["2030-12-30", "12:00"],
            "date_definitions-0-end": ["2031-06-29", "12:01"],
            "event_place": place_id,
        },
    )

    utils.assert_response_error_message(
        response,
        "Eine Veranstaltung darf maximal 180 Tage dauern",
    )


@pytest.mark.parametrize("allday", [True, False])
def test_duplicate(client, app, utils: UtilActions, seeder: Seeder, mocker, allday):
    user_id, admin_unit_id = seeder.setup_base()
    template_event_id = seeder.create_event(admin_unit_id, allday=allday)

    url = utils.get_url(
        "manage_admin_unit.event_create",
        id=admin_unit_id,
        template_id=template_event_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(url, response, {})
    utils.assert_response_redirect(response, "event_actions", event_id=2)

    with app.app_context():
        from project.models import Event

        events = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .all()
        )
        assert len(events) == 2

        assert events[1].category.name == events[0].category.name
        assert (
            events[1].date_definitions[0].allday == events[0].date_definitions[0].allday
        )


def test_actions(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("event_actions", event_id=event_id)
    response = utils.get_ok(url)

    # Nutzer ist alleine auf der Welt. Deshalb darf es keine Referenz-Links geben
    assert b"Empfehlung anfragen" not in response.data
    assert b"Veranstaltung empfehlen" not in response.data

    event_id = seeder.create_event(admin_unit_id, draft=True)
    url = utils.get_url("event_actions", event_id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    utils.login()
    utils.get_ok(url)

    _, _, event_id = seeder.create_event_unverified()
    url = utils.get_url("event_actions", event_id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)


def test_actions_withReferenceRequestLink(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url("event_actions", event_id=event_id)
    response = utils.get_ok(url)

    # 'Empfehlung anfragen' erlaubt: Referenz-Anfrage an andere AdminUnit
    assert b"Empfehlung anfragen" in response.data

    # Es gibt keine andere AdminUnit, bei der der aktuelle Nutzer Mitglied ist. Deshalb kann er die Veranstaltung nicht empfehlen.
    assert b"Veranstaltung empfehlen" not in response.data


def test_actions_unverifiedWithoutReferenceRequestLink(
    seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base(admin_unit_verified=False)
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url("event_actions", event_id=event_id)
    response = utils.get_ok(url)

    # 'Empfehlung anfragen' nicht erlaubt
    assert b"Empfehlung anfragen" not in response.data


def test_actions_withReferenceLink(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(
        other_user_id, "Other Crew", verified=True
    )
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("event_actions", event_id=event_id)
    response = utils.get_ok(url)

    # 'Empfehlung anfragen' nicht erlaubt: Der aktuelle Nutzer ist nicht Mitglied der anderen AdminUnit.
    assert b"Empfehlung anfragen" not in response.data

    # Referenz auf Veranstaltung der anderen AdminUnit erlaubt
    assert b"Veranstaltung empfehlen" in response.data


@pytest.mark.parametrize(
    "variant", ["normal", "db_error", "add_date_definition", "remove_date_definition"]
)
def test_update(client, seeder: Seeder, utils: UtilActions, app, mocker, variant):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    if variant == "remove_date_definition":
        seeder.add_event_date_definition(event_id)

    url = utils.get_url(
        "manage_admin_unit.event_update", id=admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    utils.ajax_lookup(url, "photo-license")

    if variant == "db_error":
        utils.mock_db_commit(mocker)

    data = {
        "name": "Neuer Name",
    }

    if variant == "add_date_definition":
        data["date_definitions-1-start"] = ["2030-12-31", "14:00"]

    if variant == "remove_date_definition":
        data["date_definitions-1-csrf_token"] = None
        data["date_definitions-1-start"] = None
        data["date_definitions-1-end"] = None
        data["date_definitions-1-allday"] = None
        data["date_definitions-1-recurrence_rule"] = None

    response = utils.post_form(
        url,
        response,
        data,
    )

    if variant == "db_error":
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.events", id=admin_unit_id
    )

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Neuer Name")
            .first()
        )
        assert event is not None

        if variant == "add_date_definition":
            assert len(event.date_definitions) == 2
        else:
            assert len(event.date_definitions) == 1


def test_update_co_organizers(client, seeder: Seeder, utils: UtilActions, app):
    user_id, admin_unit_id = seeder.setup_base()
    event_id, organizer_a_id, organizer_b_id = seeder.create_event_with_co_organizers(
        admin_unit_id
    )

    url = utils.get_url(
        "manage_admin_unit.event_update", id=admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Neuer Name",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.events", id=admin_unit_id
    )


@pytest.mark.parametrize("db_error", [True, False])
def test_delete(client, seeder: Seeder, utils: UtilActions, app, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_delete", id=admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {},
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.events", id=admin_unit_id
    )

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        assert event is None


def test_rrule(client, seeder: Seeder, utils: UtilActions, app):
    url = utils.get_url("event_rrule")
    response = utils.post_json(
        url,
        {
            "year": 2020,
            "month": 11,
            "day": 25,
            "rrule": "RRULE:FREQ=DAILY;COUNT=7",
            "start": 0,
        },
    )
    json = response.json

    assert json["batch"]["batch_size"] == 10

    occurence = json["occurrences"][0]
    assert occurence["date"] == "20201125T000000"
    assert occurence["formattedDate"] == '"25.11.2020"'


def test_rrule_bad_request(client, seeder: Seeder, utils: UtilActions, app):
    url = utils.get_url("event_rrule")
    response = utils.post_json(
        url,
        {
            "year": 2020,
            "month": 11,
            "day": 25,
            "rrule": "RRULE:FREQ=DAILY;COUNT=7bad",
            "start": 0,
        },
    )
    utils.assert_response_bad_request(response)


def test_report(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("event_report", event_id=event_id)
    utils.get_ok(url)


def test_ical(client, seeder: Seeder, utils: UtilActions):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    # Default
    event_id = seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())
    url = utils.get_url("event_ical", id=event_id)
    utils.get_ok(url)

    # Draft
    draft_id = seeder.create_event(
        admin_unit_id,
        draft=True,
        start=create_berlin_date(2020, 1, 2, 14, 30),
        end=create_berlin_date(2020, 1, 3, 14, 30),
    )
    url = utils.get_url("event_ical", id=draft_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    utils.login()
    utils.get_ok(url)

    # Unverified
    _, _, unverified_id = seeder.create_event_unverified()
    url = utils.get_url("event_ical", id=unverified_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    # All-day single day
    allday_id = seeder.create_event(
        admin_unit_id, allday=True, start=create_berlin_date(2020, 1, 2, 14, 30)
    )
    url = utils.get_url("event_ical", id=allday_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "DTSTART;VALUE=DATE:20200102")
    utils.assert_response_contains_not(response, "DTEND;VALUE=DATE:")

    # All-day multiple days
    allday_id = seeder.create_event(
        admin_unit_id,
        allday=True,
        start=create_berlin_date(2020, 1, 2, 14, 30),
        end=create_berlin_date(2020, 1, 3, 14, 30),
    )
    url = utils.get_url("event_ical", id=allday_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "DTSTART;VALUE=DATE:20200102")
    utils.assert_response_contains(response, "DTEND;VALUE=DATE:20200104")

    # Recurrence rule
    event_with_recc_id = seeder.create_event(
        admin_unit_id, recurrence_rule="RRULE:FREQ=DAILY;COUNT=7"
    )
    url = utils.get_url("event_ical", id=event_with_recc_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "FREQ=DAILY;COUNT=7")
