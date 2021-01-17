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
