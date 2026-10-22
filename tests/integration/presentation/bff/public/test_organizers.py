def _url(organizer_id):
    return f"/bff/public/organizers/{organizer_id}"


def _update_organizer(app, db, organizer_id, **values):
    from project.infrastructure.models import EventOrganizer

    with app.app_context():
        organizer = db.session.get(EventOrganizer, organizer_id)
        for key, value in values.items():
            if key in ("street", "postalCode", "city"):
                setattr(organizer.location, key, value)
            else:
                setattr(organizer, key, value)
        db.session.commit()


def test_get_organizer_anonymous(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    image_id = seeder.upsert_default_image()
    _update_organizer(
        app,
        db,
        organizer_id,
        url="https://organizer.test",
        email="info@organizer.test",
        phone="0123",
        fax="0456",
        street="Main St 1",
        postalCode="38640",
        city="Goslar",
        logo_id=image_id,
    )

    body = utils.get_json_ok(_url(organizer_id)).json

    assert body["id"] == organizer_id
    assert body["name"] == "Meine Crew"
    assert body["url"] == "https://organizer.test"
    assert body["email"] == "info@organizer.test"
    assert body["phone"] == "0123"
    assert body["fax"] == "0456"
    assert body["location"] == {
        "street": "Main St 1",
        "postal_code": "38640",
        "city": "Goslar",
    }
    assert f"/image/{image_id}" in body["logo_url"]
    assert "s=120" in body["logo_url"]
    assert body["organization"] == {"id": admin_unit_id, "name": "Meine Crew"}
    assert body["ical_url"].startswith("http")
    assert body["ical_url"].endswith(f"/organizers/{organizer_id}/ical")


def test_get_organizer_without_optional_data(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    _update_organizer(app, db, organizer_id, street=None, postalCode=None, city=None)

    body = utils.get_json_ok(_url(organizer_id)).json

    assert body["location"] is None
    assert body["logo_url"] is None
    assert body["url"] is None


def test_get_organizer_logged_in(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=True)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    utils.get_json_ok(_url(organizer_id))


def test_get_organizer_not_found(client, seeder, utils):
    seeder.setup_base(log_in=False)

    response = utils.get_json(_url(4711))

    utils.assert_response_notFound(response)
    assert response.json["name"] == "Not Found"
