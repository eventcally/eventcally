import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_create_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_organizer_create", id=admin_unit_id)
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data
    assert b"manage" in response.data


def test_update_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_organizer_update",
        id=admin_unit_id,
        event_organizer_id=organizer_id,
    )
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data


def test_update_unknown_organizer(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url(
        "manage_admin_unit.event_organizer_update",
        id=admin_unit_id,
        event_organizer_id=4711,
    )
    utils.assert_response_notFound(utils.get(url))


def test_update_otherAdminUnit(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    url = utils.get_url(
        "manage_admin_unit.event_organizer_update",
        id=other_admin_unit_id,
        event_organizer_id=organizer_id,
    )
    utils.get_unauthorized(url)


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_delete(client, seeder, utils, app, db, mocker, db_error, non_match):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mein Organisator")

    url = utils.get_url(
        "manage_admin_unit.event_organizer_delete",
        id=admin_unit_id,
        event_organizer_id=organizer_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_name = "Mein Organisator"

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
            response,
            "Der eingegebene Name entspricht nicht dem Namen des Veranstalters",
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_organizers", id=admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        assert organizer is None


def test_organizer(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("main.organizer", id=organizer_id)
    response = utils.get_ok(url)

    assert b'id="boot"' in response.data
    assert b"<title>Meine Crew" in response.data


def test_organizer_boot_docs_url(app, client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    url = utils.get_url("main.organizer", id=organizer_id)

    app.config["DOCS_URL"] = None
    assert b'"docsUrl": null' in utils.get_ok(url).data

    app.config["DOCS_URL"] = "https://docs.example.org"
    assert b'"docsUrl": "https://docs.example.org"' in utils.get_ok(url).data


def test_organizer_not_found(client, seeder, utils):
    seeder.setup_base(log_in=False)

    url = utils.get_url("main.organizer", id=4711)
    utils.assert_response_notFound(utils.get(url))


def test_organizers_index_gone(client, utils):
    utils.assert_response_notFound(utils.get("/organizers"))


def test_ical(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())
    url = utils.get_url("main.organizer_ical", id=admin_unit_id)
    utils.get_ok(url)


def _list_url(utils, admin_unit_id, **kwargs):
    return utils.get_url(
        "manage_admin_unit.event_organizers", id=admin_unit_id, **kwargs
    )


def _assert_order(response, *names):
    table = response.data[response.data.index(b"<table") :]
    positions = [table.index(name.encode()) for name in names]
    assert positions == sorted(positions), names


@pytest.fixture
def listed_organizers(app, db, seeder):
    from datetime import datetime

    from sqlalchemy import text

    _, admin_unit_id = seeder.setup_base()
    ids = {
        "meine_crew": seeder.upsert_default_event_organizer(admin_unit_id),
        "alpha": seeder.upsert_event_organizer(admin_unit_id, "Alpha Org"),
        "bravo": seeder.upsert_event_organizer(admin_unit_id, "Bravo Org"),
    }
    event_ids = [seeder.create_event(admin_unit_id) for _ in range(3)]

    with app.app_context():
        for key, created_at in [
            ("meine_crew", datetime(2026, 1, 1)),
            ("alpha", datetime(2026, 3, 1)),
            ("bravo", datetime(2026, 2, 1)),
        ]:
            db.session.execute(
                text("UPDATE eventorganizer SET created_at = :c WHERE id = :id"),
                {"c": created_at, "id": ids[key]},
            )
        db.session.execute(
            text("UPDATE event SET organizer_id = :organizer_id WHERE id IN :ids"),
            {"organizer_id": ids["bravo"], "ids": tuple(event_ids[:2])},
        )
        db.session.commit()

    return admin_unit_id, ids


@pytest.mark.parametrize(
    "sort, expected",
    [
        (None, ["Alpha Org", "Bravo Org", "Meine Crew"]),
        ("name", ["Alpha Org", "Bravo Org", "Meine Crew"]),
        ("-last_modified_at", ["Alpha Org", "Bravo Org", "Meine Crew"]),
        ("-number_of_events", ["Bravo Org", "Meine Crew", "Alpha Org"]),
        ("unknown", ["Alpha Org", "Bravo Org", "Meine Crew"]),
    ],
)
def test_list_sort(client, utils, listed_organizers, sort, expected):
    admin_unit_id, _ = listed_organizers
    kwargs = {"sort": sort} if sort else {}

    response = utils.get_ok(_list_url(utils, admin_unit_id, **kwargs))

    _assert_order(response, *expected)


def test_list_keyword(client, utils, listed_organizers):
    admin_unit_id, _ = listed_organizers

    response = utils.get_ok(_list_url(utils, admin_unit_id, keyword="org"))

    assert b"Alpha Org" in response.data
    assert b"Bravo Org" in response.data
    table = response.data[response.data.index(b"<table") :]
    assert b"Meine Crew" not in table


def test_list_renders_list_actions(client, utils, listed_organizers):
    admin_unit_id, ids = listed_organizers

    response = utils.get_ok(_list_url(utils, admin_unit_id))

    update_url = utils.get_url(
        "manage_admin_unit.event_organizer_update",
        id=admin_unit_id,
        event_organizer_id=ids["bravo"],
    )
    assert update_url.encode() in response.data


def test_list_pages_by_fifty(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    for i in range(60):
        seeder.upsert_event_organizer(admin_unit_id, "Organizer %02d" % i)

    # The list's own page size wins over a per_page query arg.
    response = utils.get_ok(_list_url(utils, admin_unit_id, page=2, per_page=5))

    assert b"Organizer 48" not in response.data
    assert b"Organizer 49" in response.data  # 61 organizers incl. "Meine Crew"
    assert b"Organizer 59" in response.data

    response = utils.get(_list_url(utils, admin_unit_id, page=3))
    utils.assert_response_notFound(response)
