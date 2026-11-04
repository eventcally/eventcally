import pytest

FORMS_URL = "/bff/manage/organizations/{}/event-places"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/event_place/create")


def _flashes(client):
    with client.session_transaction() as session:
        return [(category, str(message)) for category, message in session["_flashes"]]


def _body(**values):
    body = dict(
        name="Neuer Ort",
        url="https://example.org",
        description="Beschreibung",
        location=dict(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            state="Niedersachsen",
            latitude=51.9,
            longitude=10.4,
        ),
        photo=None,
    )
    body.update(values)
    return body


def _photo(seeder, **values):
    photo = dict(
        image_base64=seeder.get_default_image_upload_base64(),
        copyright_text="Me",
        license_id=None,
    )
    photo.update(values)
    return photo


def _place(app, place_id):
    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        return dict(
            name=place.name,
            url=place.url,
            description=place.description,
            street=place.location.street if place.location else None,
            city=place.location.city if place.location else None,
            photo=place.photo and (place.photo.data, place.photo.copyright_text),
        )


def _find_place(app, admin_unit_id, name):
    with app.app_context():
        from project.infrastructure.models import EventPlace

        place = EventPlace.query.filter(
            EventPlace.admin_unit_id == admin_unit_id, EventPlace.name == name
        ).first()
        return place and place.id


@pytest.fixture
def setup(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    _shell(utils, admin_unit_id)
    return admin_unit_id, place_id


def _urls(admin_unit_id, place_id):
    base = FORMS_URL.format(admin_unit_id)
    return dict(
        create_form=f"{base}/create-form",
        form=f"{base}/{place_id}",
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


def test_member_without_place_write_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    # Any Vue 3 shell carries the CSRF token for the writes.
    utils.get_ok("/organizations")
    urls = _urls(admin_unit_id, place_id)

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


def test_place_of_another_organization_is_404(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    other_id = seeder.create_admin_unit(
        seeder.create_user(email="other@test.de"), name="Andere Crew"
    )
    other_place_id = seeder.upsert_event_place(other_id, "Fremder Ort")
    urls = _urls(admin_unit_id, other_place_id)

    assert utils.get_json(urls["form"]).status_code == 404
    assert utils.put_json(urls["form"], _body()).status_code == 404
    assert _place(app, other_place_id)["name"] == "Fremder Ort"


def test_unknown_place_is_404(client, utils, setup):
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
    assert body["photo"] is None
    assert body["location"]["postalCode"] is None
    assert isinstance(body["licenses"], list)


def test_get_form(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    from project.infrastructure.models import Location

    place_id = seeder.upsert_event_place(
        admin_unit_id,
        "Mit Ort",
        Location(street="Markt 7", postalCode="38640", city="Goslar", latitude=51.9),
    )

    body = utils.get_json_ok(_urls(admin_unit_id, place_id)["form"]).json

    assert body["id"] == place_id
    assert body["name"] == "Mit Ort"
    assert body["location"]["street"] == "Markt 7"
    assert body["location"]["latitude"] == 51.9
    assert body["location"]["longitude"] is None
    assert body["photo"] is None


def test_get_form_prefills_all_fields(client, app, db, seeder, utils, setup):
    from sqlalchemy import text

    admin_unit_id, _ = setup
    place_id = seeder.upsert_event_place(admin_unit_id, "Mein Ort")
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
                "UPDATE eventplace SET url = 'https://example.com',"
                " description = 'Beschreibung', location_id = :location_id,"
                " photo_id = :image_id WHERE id = :id"
            ),
            {"location_id": location.id, "image_id": image_id, "id": place_id},
        )
        db.session.execute(
            text(
                "UPDATE image SET copyright_text = 'EventCally', license_id = 2"
                " WHERE id = :id"
            ),
            {"id": image_id},
        )
        db.session.commit()

    body = utils.get_json_ok(_urls(admin_unit_id, place_id)["form"]).json

    assert body["name"] == "Mein Ort"
    assert body["url"] == "https://example.com"
    assert body["description"] == "Beschreibung"
    assert body["location"] == dict(
        street="Markt 1",
        postalCode="38640",
        city="Goslar",
        state="Niedersachsen",
        latitude=51.9077888,
        longitude=10.4333312,
    )
    assert body["photo"]["copyright_text"] == "EventCally"
    assert body["photo"]["license_id"] == 2
    assert body["photo"]["image_base64"].startswith("data:image/png;base64,")


def test_get_form_without_location_and_photo(client, app, db, seeder, utils, setup):
    from sqlalchemy import text

    admin_unit_id, _ = setup
    place_id = seeder.upsert_event_place(admin_unit_id, "Mein Ort")

    with app.app_context():
        db.session.execute(
            text("UPDATE eventplace SET location_id = NULL WHERE id = :id"),
            {"id": place_id},
        )
        db.session.commit()

    body = utils.get_json_ok(_urls(admin_unit_id, place_id)["form"]).json

    assert body["location"]["city"] is None
    assert body["photo"] is None


def test_get_form_with_photo(client, app, seeder, utils, setup):
    admin_unit_id, place_id = setup
    urls = _urls(admin_unit_id, place_id)
    assert utils.put_json(urls["form"], _body(photo=_photo(seeder))).status_code == 200

    body = utils.get_json_ok(urls["form"]).json

    assert body["photo"]["image_base64"].startswith("data:image/png;base64,")
    assert body["photo"]["copyright_text"] == "Me"


# availability


def test_name_availability(client, utils, setup):
    admin_unit_id, place_id = setup
    url = _urls(admin_unit_id, place_id)["availability"]

    def taken(**params):
        query = "&".join(f"{key}={value}" for key, value in params.items())
        return utils.get_json_ok(f"{url}?{query}").json["name_taken"]

    assert taken(name="Meine Crew") is True
    assert taken(name="meine crew") is True
    assert taken(name="Meine Crew", exclude_id=place_id) is False
    assert taken(name="Anderer") is False
    assert utils.get_json_ok(url).json["name_taken"] is None


# create


def test_create(client, app, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(_urls(admin_unit_id, 0)["base"], _body())

    assert response.status_code == 201
    place_id = _find_place(app, admin_unit_id, "Neuer Ort")
    assert response.json == dict(
        id=place_id,
        redirect_url=utils.get_url("manage_admin_unit.event_places", id=admin_unit_id),
    )
    place = _place(app, place_id)
    assert place["street"] == "Markt 1"
    assert place["url"] == "https://example.org"
    assert place["photo"] is None
    assert _flashes(client) == [("success", "Ort erfolgreich erstellt")]


def test_create_inline_does_not_flash(client, app, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(_urls(admin_unit_id, 0)["base"], _body(inline=True))

    assert response.status_code == 201
    assert response.json["id"] == _find_place(app, admin_unit_id, "Neuer Ort")

    with client.session_transaction() as session:
        assert session.get("_flashes", []) == []


def test_create_minimal(client, app, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"],
        dict(name=" Nur Name ", url="", location={}, photo=None),
    )

    assert response.status_code == 201
    place = _place(app, _find_place(app, admin_unit_id, "Nur Name"))
    assert place["url"] is None
    assert place["city"] is None


def test_create_with_photo(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"], _body(photo=_photo(seeder))
    )

    assert response.status_code == 201
    assert _place(app, _find_place(app, admin_unit_id, "Neuer Ort"))["photo"][1] == "Me"


def test_create_taken_name_is_422(client, app, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"], _body(name="meine crew")
    )

    assert response.status_code == 422
    assert [(e["loc"], e["msg"]) for e in response.json["errors"]] == [
        (["name"], "Mit diesem Namen existiert bereits ein Ort.")
    ]
    assert _find_place(app, admin_unit_id, "meine crew") is None


@pytest.mark.parametrize(
    "values, loc",
    [
        (dict(name=" "), ["name"]),
        (dict(name="x" * 256), ["name"]),
        (dict(url="x" * 256), ["url"]),
        (dict(location=dict(postalCode="1" * 11)), ["location", "postalCode"]),
    ],
)
def test_create_invalid_is_422(client, utils, setup, values, loc):
    admin_unit_id, _ = setup

    response = utils.post_json(_urls(admin_unit_id, 0)["base"], _body(**values))

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == loc


def test_create_photo_requires_copyright(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"],
        _body(photo=_photo(seeder, copyright_text=" ")),
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["photo", "copyright_text"]


def test_create_invalid_photo_is_422(client, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id, 0)["base"],
        _body(photo=dict(image_base64="nonsense", copyright_text="Me")),
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["photo", "image_base64"]


# update


def test_update(client, app, utils, setup):
    admin_unit_id, place_id = setup

    response = utils.put_json(_urls(admin_unit_id, place_id)["form"], _body())

    assert response.status_code == 200
    assert response.json == dict(
        id=place_id,
        redirect_url=utils.get_url("manage_admin_unit.event_places", id=admin_unit_id),
    )
    place = _place(app, place_id)
    assert place["name"] == "Neuer Ort"
    assert place["street"] == "Markt 1"
    assert _flashes(client) == [("success", "Ort erfolgreich aktualisiert")]


def test_update_keeps_own_name(client, app, utils, setup):
    admin_unit_id, place_id = setup

    response = utils.put_json(
        _urls(admin_unit_id, place_id)["form"], _body(name="Meine Crew")
    )

    assert response.status_code == 200


def test_update_taken_name_is_422(client, seeder, utils, setup):
    admin_unit_id, place_id = setup
    seeder.upsert_event_place(admin_unit_id, "Andere")

    response = utils.put_json(
        _urls(admin_unit_id, place_id)["form"], _body(name="ANDERE")
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]


@pytest.mark.parametrize("change_location", [True, False])
def test_update_location_event(client, app, seeder, utils, setup, change_location):
    admin_unit_id, _ = setup
    from project.infrastructure.models import Location

    place_id = seeder.upsert_event_place(
        admin_unit_id,
        "Place",
        Location(
            street="Markt 7",
            postalCode="38640",
            city="Goslar",
            latitude=51.9077888,
            longitude=10.4333312,
        ),
    )
    url = _urls(admin_unit_id, place_id)["form"]
    body = utils.get_json_ok(url).json
    save = dict(
        name=body["name"],
        url=body["url"],
        description=body["description"],
        location=body["location"],
        photo=body["photo"],
    )
    app.test_event_dispatcher.events.clear()

    if change_location:
        save["location"]["street"] = "Neue Straße 1"

    assert utils.put_json(url, save).status_code == 200

    with app.app_context():
        from project.domain.events.event_place_updated import EventPlaceUpdated

        event = app.test_event_dispatcher.get_first_event_by_type(EventPlaceUpdated)

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


def test_update_photo_keep_replace_remove(client, app, seeder, utils, setup):
    admin_unit_id, place_id = setup
    url = _urls(admin_unit_id, place_id)["form"]

    assert utils.put_json(url, _body(photo=_photo(seeder))).status_code == 200
    stored = _place(app, place_id)["photo"]
    assert stored[1] == "Me"

    # Keep: no image_base64, the copyright text may change.
    keep = dict(image_base64=None, copyright_text="Other", license_id=None)
    assert utils.put_json(url, _body(photo=keep)).status_code == 200
    assert _place(app, place_id)["photo"] == (stored[0], "Other")

    # Replace
    replace = _photo(seeder, copyright_text="New")
    assert utils.put_json(url, _body(photo=replace)).status_code == 200
    assert _place(app, place_id)["photo"][1] == "New"

    # Remove
    assert utils.put_json(url, _body(photo=None)).status_code == 200
    assert _place(app, place_id)["photo"] is None


def test_update_keep_requires_copyright(client, seeder, utils, setup):
    admin_unit_id, place_id = setup
    url = _urls(admin_unit_id, place_id)["form"]
    assert utils.put_json(url, _body(photo=_photo(seeder))).status_code == 200

    keep = dict(image_base64=None, copyright_text="", license_id=None)
    response = utils.put_json(url, _body(photo=keep))

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["photo", "copyright_text"]


# list


def _list_url(admin_unit_id, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{FORMS_URL.format(admin_unit_id)}/list?{query}"


def _names(response):
    assert response.status_code == 200, response.json
    return [item["name"] for item in response.json["items"]]


def _exists(app, place_id):
    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import EventPlace

        return db.session.get(EventPlace, place_id) is not None


@pytest.fixture
def listed_places(app, db, seeder, utils):
    from datetime import datetime

    from sqlalchemy import text

    _, admin_unit_id = seeder.setup_base()
    ids = {
        "meine_crew": seeder.upsert_default_event_place(admin_unit_id),
        "alpha": seeder.upsert_event_place(admin_unit_id, "Alpha Halle"),
        "bravo": seeder.upsert_event_place(admin_unit_id, "Bravo Halle"),
    }
    event_ids = [seeder.create_event(admin_unit_id) for _ in range(3)]

    with app.app_context():
        for name, created_at in [
            ("Meine Crew", datetime(2026, 1, 1)),
            ("City", datetime(2026, 1, 2)),
            ("Alpha Halle", datetime(2026, 3, 1)),
            ("Bravo Halle", datetime(2026, 2, 1)),
        ]:
            db.session.execute(
                text("UPDATE eventplace SET created_at = :c WHERE name = :name"),
                {"c": created_at, "name": name},
            )
        db.session.execute(
            text("UPDATE event SET event_place_id = :place_id WHERE id IN :ids"),
            {"place_id": ids["bravo"], "ids": tuple(event_ids[:2])},
        )
        db.session.commit()

    _shell(utils, admin_unit_id)
    return admin_unit_id, ids


@pytest.mark.parametrize(
    "sort, expected",
    [
        (None, ["Alpha Halle", "Bravo Halle", "City", "Meine Crew"]),
        ("name", ["Alpha Halle", "Bravo Halle", "City", "Meine Crew"]),
        ("-last_modified_at", ["Alpha Halle", "Bravo Halle", "City", "Meine Crew"]),
        ("-number_of_events", ["Bravo Halle", "Meine Crew", "Alpha Halle", "City"]),
    ],
)
def test_list_sort(client, utils, listed_places, sort, expected):
    admin_unit_id, _ = listed_places
    params = {"sort": sort} if sort else {}

    assert _names(utils.get_json(_list_url(admin_unit_id, **params))) == expected


def test_list_unknown_sort_is_422(client, utils, listed_places):
    admin_unit_id, _ = listed_places

    assert utils.get_json(_list_url(admin_unit_id, sort="unknown")).status_code == 422


def test_list_keyword(client, utils, listed_places):
    admin_unit_id, _ = listed_places

    response = utils.get_json(_list_url(admin_unit_id, keyword="halle"))

    assert _names(response) == ["Alpha Halle", "Bravo Halle"]


def test_list_items(client, app, db, seeder, utils):
    from project.infrastructure.models import EventPlace, Location

    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    place_id = seeder.upsert_event_place(admin_unit_id, "Mit Foto")
    seeder.upsert_event_place(admin_unit_id, "Ohne Foto")
    image_id = seeder.upsert_default_image()

    with app.app_context():
        place = db.session.get(EventPlace, place_id)
        place.photo_id = image_id
        place.location = Location(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            latitude="51.9077888",
            longitude="10.4333312",
        )
        db.session.commit()

    response = utils.get_json(_list_url(admin_unit_id, keyword="foto"))

    assert _names(response) == ["Mit Foto", "Ohne Foto"]
    assert response.json["can_write"] is True
    with_photo, without_photo = response.json["items"]
    assert with_photo["id"] == place_id
    assert with_photo["location"] == "Markt 1, 38640 Goslar"
    assert with_photo["has_photo"] is True
    assert with_photo["has_coordinates"] is True
    assert with_photo["number_of_events"] == 0
    assert with_photo["last_modified_at"]
    assert without_photo["location"] is None
    assert without_photo["has_photo"] is False
    assert without_photo["has_coordinates"] is False


def test_list_pages_by_fifty(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    for i in range(60):
        seeder.upsert_event_place(admin_unit_id, "Place %02d" % i)

    response = utils.get_json(_list_url(admin_unit_id, page=2))
    names = _names(response)

    assert response.json["per_page"] == 50
    assert response.json["total"] == 61  # incl. "City"
    assert "Place 48" not in names
    assert "Place 49" in names
    assert "Place 59" in names
    assert utils.get_json(_list_url(admin_unit_id, page=3)).status_code == 404


def test_list_only_has_own_places(client, seeder, utils, setup):
    admin_unit_id, _ = setup
    other_id = seeder.create_admin_unit(
        seeder.create_user(email="other@test.de"), name="Andere Crew"
    )
    seeder.upsert_event_place(other_id, "Fremder Ort")

    assert "Fremder Ort" not in _names(utils.get_json(_list_url(admin_unit_id)))
    assert utils.get_json(_list_url(other_id)).status_code == 403


def test_list_access(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    assert utils.get_json(_list_url(admin_unit_id)).status_code == 401

    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    assert utils.get_json(_list_url(admin_unit_id)).status_code == 403


# delete


def _delete(utils, admin_unit_id, place_id, name):
    return utils.post_json(
        f"{FORMS_URL.format(admin_unit_id)}/{place_id}/delete", {"name": name}
    )


def test_delete(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    place_id = seeder.upsert_event_place(admin_unit_id, "Mein Ort")

    # The comparison ignores the case, like the old form.
    response = _delete(utils, admin_unit_id, place_id, "mein ort")

    assert response.status_code == 200
    assert response.json == {"message": "Ort erfolgreich gelöscht"}
    assert not _exists(app, place_id)


def test_delete_name_mismatch_is_422(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    place_id = seeder.upsert_event_place(admin_unit_id, "Mein Ort")

    response = _delete(utils, admin_unit_id, place_id, "Falscher Name")

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]
    assert response.json["errors"][0]["msg"] == (
        "Der eingegebene Name entspricht nicht dem Namen des Ortes"
    )
    assert _exists(app, place_id)


def test_delete_without_name_is_422(client, utils, setup):
    admin_unit_id, place_id = setup

    assert _delete(utils, admin_unit_id, place_id, "").status_code == 422


def test_delete_db_error_is_400(client, app, seeder, utils, mocker, setup):
    admin_unit_id, _ = setup
    place_id = seeder.upsert_event_place(admin_unit_id, "Mein Ort")
    utils.mock_db_commit(mocker)

    response = _delete(utils, admin_unit_id, place_id, "Mein Ort")

    assert response.status_code == 400
    assert response.json["name"] == "InfrastructureError"


def test_delete_of_another_organization_is_404(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    other_id = seeder.create_admin_unit(
        seeder.create_user(email="other@test.de"), name="Andere Crew"
    )
    other_place_id = seeder.upsert_event_place(other_id, "Fremd")

    assert _delete(utils, admin_unit_id, other_place_id, "Fremd").status_code == 404
    assert _exists(app, other_place_id)
    assert _delete(utils, admin_unit_id, 4711, "x").status_code == 404
    assert _delete(utils, other_id, other_place_id, "Fremd").status_code == 403


def test_delete_access(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    place_id = seeder.upsert_event_place(admin_unit_id, "Fremd")
    assert _delete(utils, admin_unit_id, place_id, "Fremd").status_code == 401

    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    utils.get_ok("/organizations")

    assert _delete(utils, admin_unit_id, place_id, "Fremd").status_code == 403
