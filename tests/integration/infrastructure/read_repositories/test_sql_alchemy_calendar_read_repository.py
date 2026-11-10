"""SqlAlchemyCalendarReadRepository against the database, on the read session."""

from datetime import datetime

import pytest
from sqlalchemy import text

from project.application.queries import CalendarSort, ListCalendarsQuery


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.calendar_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


@pytest.fixture
def calendars(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    ids = {
        "alpha": seeder.create_calendar(admin_unit_id, "Alpha"),
        "sports": seeder.create_calendar(admin_unit_id, "Sports club"),
        "secret": seeder.create_calendar(admin_unit_id, "Secret sports", private=True),
    }
    event_id = seeder.create_event(admin_unit_id)
    other_event_id = seeder.create_event(admin_unit_id, name="Other")
    seeder.create_calendar_entry(ids["sports"], event_id)
    seeder.create_calendar_entry(ids["sports"], other_event_id)
    seeder.create_calendar_entry(ids["alpha"], event_id)

    with app.app_context():
        for key, created_at in (
            ("alpha", datetime(2026, 1, 3)),
            ("sports", datetime(2026, 1, 1)),
            ("secret", datetime(2026, 1, 2)),
        ):
            db.session.execute(
                text("UPDATE calendar SET created_at = :c WHERE id = :id"),
                {"id": ids[key], "c": created_at},
            )
        db.session.commit()

    _, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Andere Crew", log_in=False
    )
    seeder.create_calendar(other_admin_unit_id, "Other crew calendar")

    return admin_unit_id, ids


def _names(page):
    return [item.name for item in page.items]


def _list(read_repo, admin_unit_id, include_private=True, **kwargs):
    return read_repo(
        "list",
        ListCalendarsQuery(admin_unit_id=admin_unit_id, **kwargs),
        include_private,
    )


def test_organization_exists(read_repo, calendars):
    admin_unit_id, _ = calendars

    assert read_repo("organization_exists", admin_unit_id) is True
    assert read_repo("organization_exists", 4711) is False


def test_list_is_scoped_to_organization_and_sorted_by_name(read_repo, calendars):
    admin_unit_id, _ = calendars

    page = _list(read_repo, admin_unit_id)

    assert _names(page) == ["Alpha", "Secret sports", "Sports club"]
    assert page.total == 3


def test_list_hides_private_calendars(read_repo, calendars):
    admin_unit_id, _ = calendars

    page = _list(read_repo, admin_unit_id, include_private=False)

    assert _names(page) == ["Alpha", "Sports club"]
    assert page.total == 2


def test_list_counts_events(read_repo, calendars):
    admin_unit_id, _ = calendars

    page = _list(read_repo, admin_unit_id)

    assert {item.name: item.number_of_events for item in page.items} == {
        "Alpha": 1,
        "Secret sports": 0,
        "Sports club": 2,
    }


def test_name_ranks_prefix_matches_first(read_repo, calendars):
    admin_unit_id, _ = calendars

    assert _names(_list(read_repo, admin_unit_id, name="sports")) == [
        "Sports club",
        "Secret sports",
    ]


def test_keyword_filters(read_repo, calendars):
    admin_unit_id, _ = calendars

    assert _names(_list(read_repo, admin_unit_id, keyword="^alp")) == ["Alpha"]


@pytest.mark.parametrize(
    "sort, expected",
    [
        (CalendarSort.name, ["Alpha", "Secret sports", "Sports club"]),
        (CalendarSort.created_at_desc, ["Alpha", "Secret sports", "Sports club"]),
        (CalendarSort.updated_at_desc, ["Alpha", "Secret sports", "Sports club"]),
        (
            CalendarSort.last_modified_at_desc,
            ["Alpha", "Secret sports", "Sports club"],
        ),
        (
            CalendarSort.number_of_events_desc,
            ["Sports club", "Alpha", "Secret sports"],
        ),
    ],
)
def test_sort(read_repo, calendars, sort, expected):
    admin_unit_id, _ = calendars

    assert _names(_list(read_repo, admin_unit_id, sort=sort)) == expected


def test_get(read_repo, calendars):
    admin_unit_id, ids = calendars

    calendar = read_repo("get", ids["secret"])

    assert calendar.name == "Secret sports"
    assert calendar.private is True
    assert calendar.admin_unit_id == admin_unit_id
    assert calendar.admin_unit.name == "Meine Crew"
    assert read_repo("get", 4711) is None


def test_is_name_taken(read_repo, calendars):
    admin_unit_id, ids = calendars

    assert read_repo("is_name_taken", admin_unit_id, "alpha") is True
    assert (
        read_repo("is_name_taken", admin_unit_id, "alpha", exclude_id=ids["alpha"])
        is False
    )
    assert read_repo("is_name_taken", admin_unit_id, "Other crew calendar") is False


def test_get_filter_infos(read_repo, calendars):
    admin_unit_id, ids = calendars

    infos = read_repo("get_filter_infos", [ids["alpha"], ids["secret"], 4711])

    assert {(i.id, i.admin_unit_id, i.private) for i in infos} == {
        (ids["alpha"], admin_unit_id, False),
        (ids["secret"], admin_unit_id, True),
    }
