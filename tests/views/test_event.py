import pytest


def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("event", event_id=event_id)
    utils.get_ok(url)


@pytest.mark.parametrize("db_error", [True, False])
def test_create(client, app, utils, seeder, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "start": ["2030-12-31", "23", "59"],
            "event_place_id": place_id,
            "organizer_id": organizer_id,
            "photo-image_base64": seeder.get_default_image_upload_base64(),
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit_events", id=admin_unit_id
    )

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        assert event is not None


def test_create_newPlaceAndOrganizer(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "start": ["2030-12-31", "23", "59"],
            "organizer_choice": 2,
            "new_organizer-name": "Neuer Veranstalter",
            "event_place_choice": 2,
            "new_event_place-name": "Neuer Ort",
        },
    )
    utils.assert_response_redirect(
        response, "manage_admin_unit_events", id=admin_unit_id
    )

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        assert event is not None


def test_create_missingName(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {},
    )

    utils.assert_response_error_message(response)


def test_create_missingPlace(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "start": ["2030-12-31", "23", "59"],
        },
    )

    utils.assert_response_error_message(response)


def test_create_missingOrganizer(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "start": ["31.12.2030", "23", "59"],
            "event_place_id": place_id,
            "organizer_id": organizer_id,
        },
    )

    utils.assert_response_error_message(response)


def test_create_invalidDateFormat(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "description": "Beschreibung",
            "start": ["2030-12-31", "23", "59"],
            "event_place_id": place_id,
        },
    )

    utils.assert_response_error_message(response)


def test_create_startAfterEnd(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "start": ["2030-12-31", "23", "59"],
            "end": ["2030-12-31", "23", "58"],
            "event_place_id": place_id,
        },
    )

    utils.assert_response_error_message(
        response,
        b"Der Start muss vor dem Ende sein",
    )


def test_create_DurationMoreThan24Hours(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
            "start": ["2030-12-30", "12", "00"],
            "end": ["2030-12-31", "12", "01"],
            "event_place_id": place_id,
        },
    )

    utils.assert_response_error_message(
        response,
        b"Eine Veranstaltung darf maximal 24 Stunden dauern",
    )


def test_duplicate(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    template_event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url(
        "event_create_for_admin_unit_id",
        id=admin_unit_id,
        template_id=template_event_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(url, response, {})
    utils.assert_response_redirect(
        response, "manage_admin_unit_events", id=admin_unit_id
    )

    with app.app_context():
        from project.models import Event

        events = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .all()
        )
        assert len(events) == 2


@pytest.mark.parametrize("free_text", [True, False])
def test_create_fromSuggestion(client, app, utils, seeder, mocker, free_text):
    user_id, admin_unit_id = seeder.setup_base()
    suggestion_id = seeder.create_event_suggestion(admin_unit_id, free_text)

    url = utils.get_url(
        "event_create_for_admin_unit_id",
        id=admin_unit_id,
        event_suggestion_id=suggestion_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(url, response, {})
    utils.assert_response_redirect(
        response, "manage_admin_unit_events", id=admin_unit_id
    )

    with app.app_context():
        from project.models import Event, EventSuggestion

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Vorschlag")
            .first()
        )
        assert event is not None

        suggestion = EventSuggestion.query.get(suggestion_id)
        assert suggestion is not None
        assert suggestion.verified
        assert suggestion.event_id == event.id


def test_create_verifiedSuggestionRedirectsToReviewStatus(
    client, app, utils, seeder, mocker
):
    user_id, admin_unit_id = seeder.setup_base()
    suggestion_id = seeder.create_event_suggestion(admin_unit_id)

    url = utils.get_url(
        "event_create_for_admin_unit_id",
        id=admin_unit_id,
        event_suggestion_id=suggestion_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(url, response, {})
    utils.assert_response_redirect(
        response, "manage_admin_unit_events", id=admin_unit_id
    )

    response = client.get(url)
    utils.assert_response_redirect(
        response, "event_suggestion_review_status", event_suggestion_id=suggestion_id
    )


@pytest.mark.parametrize("db_error", [True, False])
def test_update(client, seeder, utils, app, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("event_update", event_id=event_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Neuer Name",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit_events", id=admin_unit_id
    )

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Neuer Name")
            .first()
        )
        assert event is not None


@pytest.mark.parametrize("db_error", [True, False])
def test_delete(client, seeder, utils, app, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("event_delete", event_id=event_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Name",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit_events", id=admin_unit_id
    )

    with app.app_context():
        from project.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        assert event is None


def test_delete_nameDoesNotMatch(client, seeder, utils, app, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("event_delete", event_id=event_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Falscher Name",
        },
    )

    utils.assert_response_error_message(
        response, b"Der eingegebene Name entspricht nicht dem Namen der Veranstaltung"
    )


def test_rrule(client, seeder, utils, app):
    url = utils.get_url("event_rrule")
    json = utils.post_json(
        url,
        {
            "year": 2020,
            "month": 11,
            "day": 25,
            "rrule": "RRULE:FREQ=DAILY;COUNT=7",
            "start": 0,
        },
    )

    assert json["batch"]["batch_size"] == 10

    occurence = json["occurrences"][0]
    assert occurence["date"] == "20201125T000000"
    assert occurence["formattedDate"] == '"25.11.2020"'
