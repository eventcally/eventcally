from datetime import timedelta


def _update_event(app, db, event_id, **values):
    from project.infrastructure.models import Event

    with app.app_context():
        event = db.session.get(Event, event_id)
        for key, value in values.items():
            setattr(event, key, value)
        db.session.commit()


def _get(utils, event_id):
    return utils.get_json_ok(f"/bff/public/events/{event_id}").json


def test_enum_values_and_labels(client, app, db, seeder, utils):
    from project.infrastructure.models import (
        EventAttendanceMode,
        EventStatus,
        EventTargetGroupOrigin,
    )

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    body = _get(utils, event_id)
    assert body["status"] == "scheduled"
    assert body["status_label"] is None
    assert body["attendance_mode"] == "offline"
    assert body["attendance_mode_label"] is None
    assert body["target_group_origin_label"] is None

    _update_event(
        app,
        db,
        event_id,
        status=EventStatus.cancelled,
        attendance_mode=EventAttendanceMode.online,
        target_group_origin=EventTargetGroupOrigin.tourist,
        booked_up=True,
        kid_friendly=True,
        age_from=6,
        age_to=12,
    )
    body = _get(utils, event_id)
    assert body["status"] == "cancelled"
    assert body["status_label"]
    assert body["attendance_mode"] == "online"
    assert body["attendance_mode_label"]
    assert body["target_group_origin_label"]
    assert body["booked_up"] is True
    assert (body["age_from"], body["age_to"]) == (6, 12)


def test_images_with_license(client, app, db, seeder, utils):
    from project.infrastructure.models import Event, License

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    image_id = seeder.upsert_default_image()
    seeder.assign_image_to_event(event_id, image_id)

    with app.app_context():
        license = License()
        license.code = "CC0"
        license.name = "CC0"
        license.url = "https://license.test"
        db.session.add(license)
        db.session.flush()
        event = db.session.get(Event, event_id)
        event.photo.license_id = license.id
        event.photo.copyright_text = "Fotograf"
        event.event_place.photo_id = seeder.upsert_default_image()
        event.admin_unit.logo_id = seeder.upsert_default_image()
        event.organizer.logo_id = seeder.upsert_default_image()
        db.session.commit()

    body = _get(utils, event_id)

    assert "/image/" in body["photo"]["url"]
    assert "s=700" in body["photo"]["url"]
    assert body["photo"]["copyright_text"] == "Fotograf"
    assert body["photo"]["license_code"] == "CC0"
    assert body["photo"]["license_url"] == "https://license.test"
    assert "s=240" in body["place"]["photo"]["url"]
    assert body["place"]["photo"]["license_code"] is None
    assert "s=120" in body["organization"]["logo"]["url"]
    assert "s=120" in body["organizer"]["logo"]["url"]


def test_place_address_and_directions(client, app, db, seeder, utils):
    from project.infrastructure.models import Event, Location

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        place = db.session.get(Event, event_id).event_place
        place.location = Location()
        place.name = "Marktplatz"
        place.location.street = "Markt 1"
        place.location.postalCode = "38640"
        place.location.city = "Goslar"
        place.url = "example.com"
        place.description = "Mitten in der Stadt"
        db.session.commit()

    place = _get(utils, event_id)["place"]

    assert place["address"] == "Markt 1, 38640 Goslar"
    assert place["directions_query"] == "Marktplatz, Markt 1, 38640 Goslar"
    assert place["url"] == "example.com"
    assert place["description"] == "Mitten in der Stadt"


def test_place_without_location(client, app, db, seeder, utils):
    from project.infrastructure.models import Event

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        event = db.session.get(Event, event_id)
        event.event_place.location = None
        event.admin_unit.location = None
        db.session.commit()

    body = _get(utils, event_id)

    assert body["place"]["address"] is None
    assert body["organization"]["address"] is None


def test_co_organizers_keep_their_order(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id, organizer_a_id, organizer_b_id = seeder.create_event_with_co_organizers(
        admin_unit_id
    )

    body = _get(utils, event_id)

    assert body["organizer"]["name"] == "Meine Crew"
    assert [o["id"] for o in body["co_organizers"]] == [organizer_a_id, organizer_b_id]


def test_custom_category_groups(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    set_id, category_id = seeder.get_one_custom_event_category_set()
    event_id = seeder.create_event(admin_unit_id, custom_category_ids=[category_id])

    groups = _get(utils, event_id)["categories"]

    assert len(groups) == 2
    assert groups[0]["label"] == "Kategorie"
    assert groups[1]["names"]


def test_event_without_categories(client, app, db, seeder, utils):
    from project.infrastructure.models import Event

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        db.session.get(Event, event_id).categories = []
        db.session.commit()

    assert _get(utils, event_id)["categories"] == []


def test_event_dates_are_listed(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.add_event_date_definition(
        event_id, start=seeder.get_now_by_minute() + timedelta(days=1)
    )

    body = _get(utils, event_id)

    assert len(body["dates"]) == 2
    assert body["start"]
    assert body["allday"] is False
