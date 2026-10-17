import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


@pytest.mark.parametrize("db_error", [True, False])
def test_create(client, app, utils: UtilActions, seeder: Seeder, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_place_create", id=admin_unit_id)
    response = utils.get_ok(url)

    # Validation
    utils.ajax_validation(url, "name", "Meine Crew 2", True)
    utils.ajax_validation(url, "name", "Meine Crew", False)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Neuer Ort",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_places", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventPlace

        place = (
            EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit_id)
            .filter(EventPlace.name == "Neuer Ort")
            .first()
        )
        assert place is not None


@pytest.mark.parametrize("db_error", [True, False])
def test_update(client, seeder: Seeder, utils: UtilActions, app, db, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=admin_unit_id,
        event_place_id=place_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Neuer Name",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_places", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place.name == "Neuer Name"


@pytest.mark.parametrize("change_location", [True, False])
def test_update_location(
    client, seeder: Seeder, utils: UtilActions, app, db, change_location
):
    _, admin_unit_id = seeder.setup_base()

    from project.models import Location

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

    url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=admin_unit_id,
        event_place_id=place_id,
    )
    response = utils.get_ok(url)

    # 1. Update location
    data = dict()
    response = utils.post_form(
        url,
        response,
        data,
    )
    app.test_event_dispatcher.events.clear()

    # 2. Update location
    response = utils.get_ok(url)

    if change_location:
        data = {
            "location-street": "Neue Straße 1",
        }
    response = utils.post_form(
        url,
        response,
        data,
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_places", id=admin_unit_id
    )

    with app.app_context():
        from project.domain.events.event_place_updated import EventPlaceUpdated

        event_place_updated = app.test_event_dispatcher.get_first_event_by_type(
            EventPlaceUpdated
        )

        if change_location:
            assert event_place_updated.model_fields_set == {
                "actor",
                "id",
                "admin_unit_id",
                "location",
            }
            assert event_place_updated.location.new.street == "Neue Straße 1"
        else:
            assert event_place_updated is None


def test_update_otherAdminUnit(client, seeder, utils, app, db):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=other_admin_unit_id,
        event_place_id=place_id,
    )
    utils.get_unauthorized(url)


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_delete(client, seeder, utils, app, db, mocker, db_error, non_match):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_event_place(admin_unit_id, "Mein Ort")

    url = utils.get_url(
        "manage_admin_unit.event_place_delete",
        id=admin_unit_id,
        event_place_id=place_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_name = "Mein Ort"

    if non_match:
        form_name = "Falscher Name"

    response = utils.post_form(
        url,
        response,
        {
            "name": form_name,
        },
    )

    if non_match:
        utils.assert_response_error_message(
            response, "Der eingegebene Name entspricht nicht dem Namen des Ortes"
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_places", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place is None


def test_create_Unauthorized(client, app, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    response = utils.get_endpoint(
        "manage_admin_unit.event_place_create", id=admin_unit_id
    )
    utils.assert_response_permission_missing(
        response, "main.manage_admin_unit", id=admin_unit_id
    )


def test_create_admin(client, app, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base(admin=True)

    url = utils.get_url("manage_admin_unit.event_place_create", id=admin_unit_id)
    utils.get_ok(url)


def test_update_name_validation(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    seeder.upsert_event_place(admin_unit_id, "Andere")

    url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=admin_unit_id,
        event_place_id=place_id,
    )
    utils.get_ok(url)

    utils.ajax_validation(url, "name", "Meine Crew", True)  # its own name
    utils.ajax_validation(url, "name", "meine crew", True)
    utils.ajax_validation(url, "name", "ANDERE", False)


def _list_url(utils, admin_unit_id, **kwargs):
    return utils.get_url("manage_admin_unit.event_places", id=admin_unit_id, **kwargs)


def _assert_order(response, *names):
    table = response.data[response.data.index(b"<table") :]
    positions = [table.index(name.encode()) for name in names]
    assert positions == sorted(positions), names


@pytest.fixture
def listed_places(app, db, seeder):
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

    return admin_unit_id, ids


@pytest.mark.parametrize(
    "sort, expected",
    [
        (None, ["Alpha Halle", "Bravo Halle", "City", "Meine Crew"]),
        ("name", ["Alpha Halle", "Bravo Halle", "City", "Meine Crew"]),
        ("-last_modified_at", ["Alpha Halle", "Bravo Halle", "City", "Meine Crew"]),
        ("-number_of_events", ["Bravo Halle", "Meine Crew", "Alpha Halle", "City"]),
        ("unknown", ["Alpha Halle", "Bravo Halle", "City", "Meine Crew"]),
    ],
)
def test_list_sort(client, utils, listed_places, sort, expected):
    admin_unit_id, _ = listed_places
    kwargs = {"sort": sort} if sort else {}

    response = utils.get_ok(_list_url(utils, admin_unit_id, **kwargs))

    _assert_order(response, *expected)


def test_list_keyword(client, utils, listed_places):
    admin_unit_id, _ = listed_places

    response = utils.get_ok(_list_url(utils, admin_unit_id, keyword="halle"))

    assert b"Alpha Halle" in response.data
    assert b"Bravo Halle" in response.data
    table = response.data[response.data.index(b"<table") :]
    assert b"Meine Crew" not in table


def test_list_renders_list_actions(client, utils, listed_places):
    admin_unit_id, ids = listed_places

    response = utils.get_ok(_list_url(utils, admin_unit_id))

    update_url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=admin_unit_id,
        event_place_id=ids["bravo"],
    )
    assert update_url.encode() in response.data


def test_list_renders_photo_and_coordinates(client, app, db, seeder, utils):
    from project.models import EventPlace, Location

    _, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_event_place(admin_unit_id, "Mit Foto")
    seeder.upsert_event_place(admin_unit_id, "Ohne Foto")
    image_id = seeder.upsert_default_image()

    with app.app_context():
        place = db.session.get(EventPlace, place_id)
        place.photo_id = image_id
        place.location = Location(
            city="Goslar", latitude="51.9077888", longitude="10.4333312"
        )
        db.session.commit()

    response = utils.get_ok(_list_url(utils, admin_unit_id))

    _assert_order(response, "Mit Foto", "Ohne Foto")
    assert b"Goslar" in response.data


def test_list_pages_by_fifty(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    for i in range(60):
        seeder.upsert_event_place(admin_unit_id, "Place %02d" % i)

    # The list's own page size wins over a per_page query arg.
    response = utils.get_ok(_list_url(utils, admin_unit_id, page=2, per_page=5))

    assert b"Place 48" not in response.data
    assert b"Place 49" in response.data  # 61 places incl. "City"
    assert b"Place 59" in response.data

    response = utils.get(_list_url(utils, admin_unit_id, page=3))
    utils.assert_response_notFound(response)
