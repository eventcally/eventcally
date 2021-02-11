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


def test_oauth2_token(client, app):
    from project.models import OAuth2Token

    token = OAuth2Token()
    token.revoked = True
    assert not token.is_refresh_token_active()

    token.revoked = False
    token.issued_at = 0
    token.expires_in = 0
    assert not token.is_refresh_token_active()
