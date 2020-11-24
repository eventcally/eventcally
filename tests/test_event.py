def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("event", event_id=event_id)
    utils.get_ok(url)


def create_data(place_id: int, organizer_id: int) -> dict:
    return {
        "name": "Name",
        "description": "Beschreibung",
        "start": ["2030-12-31", "23", "59"],
        "event_place_id": place_id,
        "organizer_id": organizer_id,
    }


def test_create(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        create_data(place_id, organizer_id),
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


def test_create_dbError(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
    response = utils.get_ok(url)

    utils.mock_db_commit(mocker)
    response = utils.post_form(
        url,
        response,
        create_data(place_id, organizer_id),
    )
    utils.assert_response_db_error(response)


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


def test_create_fromSuggestion(client, app, utils, seeder, mocker):
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
