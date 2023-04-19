def test_read(client, app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    event_list_id = seeder.create_event_list(admin_unit_id)

    url = utils.get_url("api_v1_event_list_model", id=event_list_id)
    response = utils.get_ok(url)
    assert response.json["id"] == event_list_id


def test_put(client, seeder, utils, app, db):
    _, admin_unit_id = seeder.setup_api_access()
    event_list_id = seeder.create_event_list(admin_unit_id)

    url = utils.get_url("api_v1_event_list_model", id=event_list_id)
    response = utils.put_json(url, {"name": "Neuer Name"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventList

        event_list = db.session.get(EventList, event_list_id)
        assert event_list.name == "Neuer Name"


def test_patch(client, seeder, utils, app, db):
    _, admin_unit_id = seeder.setup_api_access()
    event_list_id = seeder.create_event_list(admin_unit_id)

    url = utils.get_url("api_v1_event_list_model", id=event_list_id)
    response = utils.patch_json(url, {"name": "Neuer Name"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventList

        event_list = db.session.get(EventList, event_list_id)
        assert event_list.name == "Neuer Name"


def test_delete(client, seeder, utils, app, db):
    _, admin_unit_id = seeder.setup_api_access()
    event_list_id = seeder.create_event_list(admin_unit_id)

    url = utils.get_url("api_v1_event_list_model", id=event_list_id)
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventList

        event_list = db.session.get(EventList, event_list_id)
        assert event_list is None


def test_events(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    event_list_id = seeder.create_event_list(admin_unit_id, event_id)

    url = utils.get_url("api_v1_event_list_event_list", id=event_list_id)
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == event_id


def test_events_put(client, seeder, utils, app, db):
    _, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    event_list_id = seeder.create_event_list(admin_unit_id)

    url = utils.get_url(
        "api_v1_event_list_event_list_write", id=event_list_id, event_id=event_id
    )
    response = utils.put_json(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventList

        event_list = db.session.get(EventList, event_list_id)
        assert len(event_list.events) == 1
        assert event_list.events[0].id == event_id


def test_events_delete(client, seeder, utils, app, db):
    _, admin_unit_id = seeder.setup_api_access()
    event_id = seeder.create_event(admin_unit_id)
    event_list_id = seeder.create_event_list(admin_unit_id, event_id)

    url = utils.get_url(
        "api_v1_event_list_event_list_write", id=event_list_id, event_id=event_id
    )
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import Event, EventList

        event_list = db.session.get(EventList, event_list_id)
        assert len(event_list.events) == 0

        event = db.session.get(Event, event_id)
        assert event is not None
