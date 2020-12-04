def test_location_update_coordinate(client, app, db):
    from project.models import Location

    location = Location()
    location.latitude = 51.9077888
    location.longitude = 10.4333312
    location.update_coordinate()

    assert location.coordinate is not None


def test_event_category(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import Event

        event = Event.query.get(event_id)
        event.categories = []
        db.session.commit()

        assert event.category is None
