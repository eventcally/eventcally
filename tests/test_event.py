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

    response = utils.post_form(url, response, create_data(place_id, organizer_id))
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
