import pytest

FORMS_URL = "/bff/manage/organizations/{}/event-organizers"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/event_organizer/create")


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _body(**values):
    body = dict(
        name="Neuer Organisator",
        url="http://test.de",
        email="test@example.com",
        phone="1234567890",
        fax="0987654321",
        location=dict(
            street="Straße 1",
            postalCode="38640",
            city="Goslar",
            state="Niedersachsen",
            latitude=51.9077888,
            longitude=10.4333312,
        ),
        logo=None,
    )
    body.update(values)
    return body


def _logo(seeder, **values):
    logo = dict(
        image_base64=seeder.get_default_image_upload_base64(),
        copyright_text="EventCally",
        license_id=None,
    )
    logo.update(values)
    return logo


def _organizer(app, organizer_id):
    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        location = organizer.location
        return dict(
            name=organizer.name,
            url=organizer.url,
            email=organizer.email,
            phone=organizer.phone,
            fax=organizer.fax,
            street=location.street if location else None,
            postalCode=location.postalCode if location else None,
            city=location.city if location else None,
            latitude=(
                float(location.latitude) if location and location.latitude else None
            ),
            longitude=(
                float(location.longitude) if location and location.longitude else None
            ),
            logo=organizer.logo
            and (organizer.logo.data, organizer.logo.copyright_text),
        )


def _find_organizer(app, admin_unit_id, name):
    with app.app_context():
        from project.infrastructure.models import EventOrganizer

        organizer = EventOrganizer.query.filter(
            EventOrganizer.admin_unit_id == admin_unit_id, EventOrganizer.name == name
        ).first()
        return organizer and organizer.id


@pytest.fixture
def setup(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    _shell(utils, admin_unit_id)
    return admin_unit_id, organizer_id


def _urls(admin_unit_id, organizer_id):
    base = FORMS_URL.format(admin_unit_id)
    return dict(
        create_form=f"{base}/create-form",
        form=f"{base}/{organizer_id}",
        availability=f"{base}/name-availability",
        base=base,
    )


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    urls = _urls(admin_unit_id, 1)

    for call in (
        lambda: utils.get_json(urls["create_form"]),
        lambda: utils.get_json(urls["form"]),
        lambda: utils.get_json(urls["availability"] + "?name=x"),
        lambda: utils.post_json(urls["base"], _body()),
        lambda: utils.put_json(urls["form"], _body()),
    ):
        assert call().status_code == 401


def test_member_without_organizer_write_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    # Any Vue 3 shell carries the CSRF token for the writes.
    utils.get_ok("/organizations")
    urls = _urls(admin_unit_id, organizer_id)

    assert utils.get_json(urls["create_form"]).status_code == 403
    assert utils.get_json(urls["form"]).status_code == 403
    assert utils.get_json(urls["availability"] + "?name=x").status_code == 403
    assert utils.post_json(urls["base"], _body()).status_code == 403
    assert utils.put_json(urls["form"], _body()).status_code == 403


def test_foreign_organization_is_403(client, seeder, utils, setup):
    owner_id = seeder.create_user(email="other@test.de")
    other_id = seeder.create_admin_unit(owner_id, name="Andere Crew")
    urls = _urls(other_id, 1)

    assert utils.get_json(urls["create_form"]).status_code == 403
    assert utils.post_json(urls["base"], _body()).status_code == 403


def test_organizer_of_another_organization_is_404(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    other_id = seeder.create_admin_unit(
        seeder.create_user(email="other@test.de"), name="Andere Crew"
    )
    other_organizer_id = seeder.upsert_event_organizer(other_id, "Fremder")
    urls = _urls(admin_unit_id, other_organizer_id)

    assert utils.get_json(urls["form"]).status_code == 404
    assert utils.put_json(urls["form"], _body()).status_code == 404
    assert _organizer(app, other_organizer_id)["name"] == "Fremder"


def test_unknown_organizer_is_404(client, utils, setup):
    admin_unit_id, _ = setup

    assert utils.get_json(_urls(admin_unit_id, 4711)["form"]).status_code == 404


def test_write_requires_csrf(client, seeder):
    _, admin_unit_id = seeder.setup_base()
    urls = _urls(admin_unit_id, 1)

    response = client.post(urls["base"], json=_body())
    assert response.status_code == 400


# forms


def test_get_create_form(client, utils, setup):
    admin_unit_id, _ = setup

    body = utils.get_json_ok(_urls(admin_unit_id, 0)["create_form"]).json

    assert body["id"] is None
    assert body["name"] == ""
    assert body["logo"] is None
    assert body["email"] is None
    assert body["location"]["postalCode"] is None
    assert isinstance(body["licenses"], list)


def test_get_form_prefills_all_fields(client, app, db, seeder, utils, setup):
    from sqlalchemy import text

    admin_unit_id, _ = setup
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mein Organisator")
    image_id = seeder.upsert_default_image()

    with app.app_context():
        from project.infrastructure.models import Location

        location = Location(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            state="Niedersachsen",
            latitude="51.9077888",
            longitude="10.4333312",
        )
        db.session.add(location)
        db.session.flush()
        db.session.execute(
            text(
                "UPDATE eventorganizer SET url = 'https://example.com',"
                " email = 'info@example.com', phone = '123', fax = '456',"
                " location_id = :location_id, logo_id = :image_id WHERE id = :id"
            ),
            {"location_id": location.id, "image_id": image_id, "id": organizer_id},
        )
        db.session.execute(
            text(
                "UPDATE image SET copyright_text = 'EventCally', license_id = 2"
                " WHERE id = :id"
            ),
            {"id": image_id},
        )
        db.session.commit()

    body = utils.get_json_ok(_urls(admin_unit_id, organizer_id)["form"]).json

    assert body["id"] == organizer_id
    assert body["name"] == "Mein Organisator"
    assert body["url"] == "https://example.com"
    assert body["email"] == "info@example.com"
    assert body["phone"] == "123"
    assert body["fax"] == "456"
    assert body["location"] == dict(
        street="Markt 1",
        postalCode="38640",
        city="Goslar",
        state="Niedersachsen",
        latitude=51.9077888,
        longitude=10.4333312,
    )
    assert body["logo"]["copyright_text"] == "EventCally"
    assert body["logo"]["license_id"] == 2
    assert body["logo"]["image_base64"].startswith("data:image/png;base64,")


def test_get_form_without_location_and_logo(client, app, db, seeder, utils, setup):
    from sqlalchemy import text

    admin_unit_id, organizer_id = setup

    with app.app_context():
        db.session.execute(
            text("UPDATE eventorganizer SET location_id = NULL WHERE id = :id"),
            {"id": organizer_id},
        )
        db.session.commit()

    body = utils.get_json_ok(_urls(admin_unit_id, organizer_id)["form"]).json

    assert body["location"]["city"] is None
    assert body["logo"] is None


# availability


def test_name_availability(client, utils, setup):
    admin_unit_id, organizer_id = setup
    url = _urls(admin_unit_id, organizer_id)["availability"]

    def taken(**params):
        query = "&".join(f"{key}={value}" for key, value in params.items())
        return utils.get_json_ok(f"{url}?{query}").json["name_taken"]

    assert taken(name="Meine Crew") is True
    assert taken(name="meine crew") is True
    assert taken(name="Meine Crew", exclude_id=organizer_id) is False
    assert taken(name="Anderer") is False
    assert utils.get_json_ok(url).json["name_taken"] is None


# create


def test_create(client, app, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(_urls(admin_unit_id, 0)["base"], _body())

    assert response.status_code == 201
    organizer_id = _find_organizer(app, admin_unit_id, "Neuer Organisator")
    assert response.json == dict(
        id=organizer_id,
        redirect_url=utils.get_url(
            "manage_admin_unit.event_organizers", id=admin_unit_id
        ),
    )
    assert _organizer(app, organizer_id) == dict(
        name="Neuer Organisator",
        url="http://test.de",
        email="test@example.com",
        phone="1234567890",
        fax="0987654321",
        street="Straße 1",
        postalCode="38640",
        city="Goslar",
        latitude=51.9077888,
        longitude=10.4333312,
        logo=None,
    )
    assert _flashes(client) == [("success", "Veranstalter erfolgreich erstellt")]


def test_create_minimal(client, app, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"],
        dict(name=" Nur Name ", url="", email="", location={}, logo=None),
    )

    assert response.status_code == 201
    organizer = _organizer(app, _find_organizer(app, admin_unit_id, "Nur Name"))
    assert organizer["url"] is None
    assert organizer["email"] is None
    assert organizer["city"] is None


def test_create_with_logo(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"], _body(logo=_logo(seeder))
    )

    assert response.status_code == 201
    organizer_id = _find_organizer(app, admin_unit_id, "Neuer Organisator")
    assert _organizer(app, organizer_id)["logo"][1] == "EventCally"


def test_create_taken_name_is_422(client, app, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"], _body(name="meine crew")
    )

    assert response.status_code == 422
    assert [(e["loc"], e["msg"]) for e in response.json["errors"]] == [
        (["name"], "Mit diesem Namen existiert bereits ein Veranstalter.")
    ]
    assert _find_organizer(app, admin_unit_id, "meine crew") is None


@pytest.mark.parametrize(
    "values, loc",
    [
        (dict(name=" "), ["name"]),
        (dict(name="x" * 256), ["name"]),
        (dict(url="x" * 256), ["url"]),
        (dict(email="x" * 256), ["email"]),
        (dict(phone="x" * 256), ["phone"]),
        (dict(fax="x" * 256), ["fax"]),
        (dict(location=dict(postalCode="1" * 11)), ["location", "postalCode"]),
    ],
)
def test_create_invalid_is_422(client, utils, setup, values, loc):
    admin_unit_id, _ = setup

    response = utils.post_json(_urls(admin_unit_id, 0)["base"], _body(**values))

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == loc


def test_create_logo_too_small(client, utils, setup):
    admin_unit_id, _ = setup
    too_small = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAA"
        "CXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg=="
    )

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"],
        _body(logo=dict(image_base64=too_small, copyright_text="Me")),
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["logo", "image_base64"]


def test_create_logo_requires_copyright(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"],
        _body(logo=_logo(seeder, copyright_text=" ")),
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["logo", "copyright_text"]


# update


def test_update(client, app, utils, setup):
    admin_unit_id, organizer_id = setup

    response = utils.put_json(_urls(admin_unit_id, organizer_id)["form"], _body())

    assert response.status_code == 200
    assert response.json == dict(
        id=organizer_id,
        redirect_url=utils.get_url(
            "manage_admin_unit.event_organizers", id=admin_unit_id
        ),
    )
    organizer = _organizer(app, organizer_id)
    assert organizer["name"] == "Neuer Organisator"
    assert organizer["email"] == "test@example.com"
    assert organizer["street"] == "Straße 1"
    assert _flashes(client) == [("success", "Veranstalter erfolgreich aktualisiert")]


def test_update_keeps_own_name(client, utils, setup):
    admin_unit_id, organizer_id = setup

    response = utils.put_json(
        _urls(admin_unit_id, organizer_id)["form"], _body(name="Meine Crew")
    )

    assert response.status_code == 200


def test_update_clears_contacts(client, app, utils, setup):
    admin_unit_id, organizer_id = setup
    url = _urls(admin_unit_id, organizer_id)["form"]
    assert utils.put_json(url, _body()).status_code == 200

    cleared = _body(url="", email="", phone="", fax="", location={})
    assert utils.put_json(url, cleared).status_code == 200

    organizer = _organizer(app, organizer_id)
    assert organizer["url"] is None
    assert organizer["fax"] is None
    assert organizer["street"] is None


def test_update_taken_name_is_422(client, seeder, utils, setup):
    admin_unit_id, organizer_id = setup
    seeder.upsert_event_organizer(admin_unit_id, "Andere")

    response = utils.put_json(
        _urls(admin_unit_id, organizer_id)["form"], _body(name="ANDERE")
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]


@pytest.mark.parametrize("change_location", [True, False])
def test_update_location_event(client, app, db, seeder, utils, setup, change_location):
    from sqlalchemy import text

    admin_unit_id, organizer_id = setup

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE location SET street = 'Markt 7', \"postalCode\" = '38640',"
                " city = 'Goslar', latitude = 51.9077888, longitude = 10.4333312"
                " WHERE id = (SELECT location_id FROM eventorganizer WHERE id = :id)"
            ),
            {"id": organizer_id},
        )
        db.session.commit()

    url = _urls(admin_unit_id, organizer_id)["form"]
    body = utils.get_json_ok(url).json
    save = dict(
        name=body["name"],
        url=body["url"],
        email=body["email"],
        phone=body["phone"],
        fax=body["fax"],
        location=body["location"],
        logo=body["logo"],
    )
    app.test_event_dispatcher.events.clear()

    if change_location:
        save["location"]["street"] = "Neue Straße 1"

    assert utils.put_json(url, save).status_code == 200

    with app.app_context():
        from project.domain.events.event_organizer_updated import EventOrganizerUpdated

        event = app.test_event_dispatcher.get_first_event_by_type(EventOrganizerUpdated)

        if change_location:
            assert event.model_fields_set == {
                "actor",
                "id",
                "admin_unit_id",
                "location",
            }
            assert event.location.new.street == "Neue Straße 1"
        else:
            assert event is None


def test_update_logo_keep_replace_remove(client, app, seeder, utils, setup):
    admin_unit_id, organizer_id = setup
    url = _urls(admin_unit_id, organizer_id)["form"]

    assert utils.put_json(url, _body(logo=_logo(seeder))).status_code == 200
    stored = _organizer(app, organizer_id)["logo"]
    assert stored[1] == "EventCally"

    # Keep: no image_base64, the copyright text may change.
    keep = dict(image_base64=None, copyright_text="Other", license_id=None)
    assert utils.put_json(url, _body(logo=keep)).status_code == 200
    assert _organizer(app, organizer_id)["logo"] == (stored[0], "Other")

    # Replace
    replace = _logo(seeder, copyright_text="New")
    assert utils.put_json(url, _body(logo=replace)).status_code == 200
    assert _organizer(app, organizer_id)["logo"][1] == "New"

    # The form shows the stored logo.
    body = utils.get_json_ok(url).json
    assert body["logo"]["image_base64"].startswith("data:image/png;base64,")
    assert body["logo"]["copyright_text"] == "New"

    # Remove
    assert utils.put_json(url, _body(logo=None)).status_code == 200
    assert _organizer(app, organizer_id)["logo"] is None


def test_update_keep_requires_copyright(client, seeder, utils, setup):
    admin_unit_id, organizer_id = setup
    url = _urls(admin_unit_id, organizer_id)["form"]
    assert utils.put_json(url, _body(logo=_logo(seeder))).status_code == 200

    keep = dict(image_base64=None, copyright_text="", license_id=None)
    response = utils.put_json(url, _body(logo=keep))

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["logo", "copyright_text"]
