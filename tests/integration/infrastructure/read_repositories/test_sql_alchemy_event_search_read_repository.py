"""SqlAlchemyEventSearchReadRepository against the database, on the read session.

One deterministic event world (see `tests/event_read_seed.py`) answers every criterion.
"""

from datetime import datetime

import pytest
from sqlalchemy import event as sa_event

from project.application.queries import (
    EventSearchCriteria,
    EventSearchSort,
    ListEventDatesQuery,
    ListEventsQuery,
    PageRequest,
    TrackableCriteria,
    TrackableSort,
)
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.shared.dateutils import create_berlin_date
from tests.integration.event_read_seed import seed_event_world

PUBLIC = [
    "Past Event",
    "Other Event",
    "Full Event",
    "Weekly Jam",
    "Allday Fest",
    "Cancelled Event",
]


@pytest.fixture
def world(app, db, seeder):
    return seed_event_world(app, db, seeder)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.event_search_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def _search(
    read_repo,
    method="search_events",
    private=False,
    planned=False,
    reference=None,
    page=PageRequest(per_page=100),
    **criteria,
):
    return read_repo(
        method, EventSearchCriteria(**criteria), page, private, planned, reference
    )


def _names(page):
    return [
        getattr(item, "event", item).name if hasattr(item, "event") else item.name
        for item in page.items
    ]


def test_default_search_is_public_verified_published(read_repo, world):
    page = _search(read_repo)

    assert _names(page) == PUBLIC
    assert page.total == len(PUBLIC)


def test_planned_events_need_the_planning_right(read_repo, world):
    planned = [EventPublicStatus.planned]

    # Planned events are only found when asked for, and only by planners.
    assert _names(_search(read_repo, planned=True)) == PUBLIC
    assert _names(_search(read_repo, public_status=planned)) == []
    assert _names(_search(read_repo, planned=True, public_status=planned)) == [
        "Planned Event"
    ]


def test_private_events_of_an_organization(read_repo, world):
    page = _search(read_repo, private=True, admin_unit_id=world["a"])

    assert _names(page) == [
        "Past Event",
        "Full Event",
        "Weekly Jam",
        "Allday Fest",
        "Draft Event",
        "Planned Event",
        "Cancelled Event",
    ]

    # Not granted: the organization's drafts stay hidden.
    assert "Draft Event" not in _names(_search(read_repo, admin_unit_id=world["a"]))


def test_unverified_organizations_show_only_to_their_members(read_repo, world):
    assert "Unverified Event" not in _names(_search(read_repo))
    assert _names(_search(read_repo, private=True, admin_unit_id=world["c"])) == [
        "Unverified Event"
    ]


@pytest.mark.parametrize(
    "criteria, expected",
    [
        ({"keyword": "Jam"}, ["Weekly Jam"]),
        ({"keyword": "Goslar"}, ["Full Event"]),
        ({"keyword": "Crew"}, PUBLIC),
        ({"tags": ["music"]}, ["Full Event", "Weekly Jam"]),
        ({"tags": ["music", "live"]}, ["Full Event"]),
        ({"postal_codes": ["386", "999"]}, ["Full Event"]),
        ({"exclude_recurring": True}, [n for n in PUBLIC if n != "Weekly Jam"]),
        ({"expected_participants_min": 50}, ["Full Event"]),
        ({"expected_participants_min": 51}, []),
        ({"status": [EventStatus.cancelled]}, ["Cancelled Event"]),
        ({"public_status": [EventPublicStatus.published]}, PUBLIC),
        ({"public_status": [EventPublicStatus.draft]}, []),
        ({"latitude": 51.9, "longitude": 10.4, "distance": 20000}, ["Full Event"]),
        ({"latitude": 51.9, "longitude": 10.4, "distance": 1}, []),
    ],
)
def test_criteria(read_repo, world, criteria, expected):
    assert _names(_search(read_repo, **criteria)) == expected


def test_criteria_by_relations(read_repo, world, app):
    full = {"Full Event"}
    place = _names(_search(read_repo, event_place_id=world["rathaus"]))
    organizer = _names(_search(read_repo, organizer_id=2))

    assert set(place) == full
    assert "Full Event" not in organizer or organizer == []
    assert set(_names(_search(read_repo, category_ids=[20]))) <= full
    assert set(_names(_search(read_repo, custom_category_set_ids=[1]))) == full
    assert _names(_search(read_repo, custom_category_set_ids=[4711])) == []


def test_internal_tags_need_the_private_right_and_an_organization(read_repo, world):
    kwargs = dict(internal_tags=["secret"], admin_unit_id=world["a"])

    assert _names(_search(read_repo, private=True, **kwargs)) == [
        "Full Event",
        "Cancelled Event",
    ]
    assert _names(_search(read_repo, private=True, **kwargs, tags=["live"])) == [
        "Full Event"
    ]
    # Ignored without the right, and with the organization's references included.
    assert len(_search(read_repo, **kwargs).items) == 5
    assert (
        len(
            _search(
                read_repo,
                private=True,
                include_admin_unit_references=True,
                **kwargs,
            ).items
        )
        >= 2
    )


def test_date_range_and_weekdays(read_repo, world):
    march_first = dict(
        date_from=create_berlin_date(2040, 3, 1),
        date_to=create_berlin_date(2040, 3, 1, 23),
    )

    assert _names(_search(read_repo, **march_first)) == ["Other Event", "Full Event"]
    assert _names(_search(read_repo, date_from=create_berlin_date(2040, 7, 1))) == [
        "Cancelled Event"
    ]
    assert _names(_search(read_repo, date_to=create_berlin_date(2021, 1, 1))) == [
        "Past Event"
    ]

    # An event spanning the range start matches through its end.
    page = _search(
        read_repo,
        method="search_event_dates",
        date_from=create_berlin_date(2040, 5, 5, 12),
        date_to=create_berlin_date(2040, 5, 5, 13),
    )
    assert _names(page) == ["Allday Fest"]

    weekday = (create_berlin_date(2040, 4, 2).weekday() + 1) % 7  # 0 = Sunday
    page = _search(read_repo, method="search_event_dates", weekdays=[weekday])
    assert {"Weekly Jam"} <= set(_names(page))
    assert (
        _names(
            _search(read_repo, method="search_event_dates", weekdays=[weekday + 100])
        )
        == []
    )


def test_event_dates_are_one_row_per_date(read_repo, world):
    page = _search(read_repo, method="search_event_dates")

    assert [(hit.event.name, hit.start.year) for hit in page.items][:3] == [
        ("Past Event", 2020),
        ("Other Event", 2040),
        ("Full Event", 2040),
    ]
    assert _names(page).count("Weekly Jam") == 3
    assert _names(page).count("Full Event") == 2
    assert page.total == len(page.items)


def test_organization_references(read_repo, world):
    admin_unit_id = world["a"]
    own = _names(_search(read_repo, admin_unit_id=admin_unit_id))
    included = _names(
        _search(
            read_repo, admin_unit_id=admin_unit_id, include_admin_unit_references=True
        )
    )
    only = _names(
        _search(read_repo, admin_unit_id=admin_unit_id, admin_unit_references_only=True)
    )

    assert "Other Event" not in own
    assert included == PUBLIC
    assert only == ["Other Event"]


def test_not_referenced_by(read_repo, world):
    names = _names(_search(read_repo, not_referenced_by_admin_unit_id=world["a"]))
    assert names == []

    names = _names(_search(read_repo, not_referenced_by_admin_unit_id=world["b"]))
    assert "Other Event" not in names
    assert "Full Event" in names


def test_sorts(read_repo, world):
    created = _names(_search(read_repo, sort=EventSearchSort.created_at_desc))
    assert created[0] == "Other Event" and created[-1] == "Full Event"

    rating = _names(_search(read_repo, sort=EventSearchSort.rating_desc))
    assert rating[0] == "Full Event"  # rating 80, the others 50

    with_reference = dict(admin_unit_id=world["a"], include_admin_unit_references=True)
    rating = _names(
        _search(read_repo, sort=EventSearchSort.rating_desc, **with_reference)
    )
    assert rating[:2] == ["Other Event", "Full Event"]  # reference rating 90 wins

    by_reference = _names(
        _search(
            read_repo, sort=EventSearchSort.reference_created_at_desc, **with_reference
        )
    )
    assert by_reference[-1] == "Other Event"  # descending puts NULLs first

    # Without a reference join the reference sort leaves the default order.
    assert (
        _names(_search(read_repo, sort=EventSearchSort.reference_created_at_desc))
        == PUBLIC
    )


def test_trackable_bounds(read_repo, world):
    criteria = TrackableCriteria(
        created_at_from=datetime(2026, 1, 3), created_at_to=datetime(2026, 1, 5)
    )

    page = _search(read_repo, trackable=criteria)
    assert 0 < page.total < len(PUBLIC)


def test_paging_reports_the_total(read_repo, world):
    page = _search(read_repo, page=PageRequest(page=2, per_page=4))

    assert _names(page) == PUBLIC[4:]
    assert page.total == len(PUBLIC)
    assert page.page == 2


def test_reference_id_of_the_calling_organization(read_repo, world):
    page = _search(read_repo, reference=world["a"])
    by_name = {item.name: item for item in page.items}

    assert by_name["Other Event"].reference_id == world["reference"]
    assert by_name["Full Event"].reference_id is None
    assert _search(read_repo).items[1].reference_id is None


def test_event_search_item_is_complete(read_repo, world):
    page = _search(read_repo, keyword="Full", private=True, admin_unit_id=world["a"])
    full = page.items[0]

    assert full.admin_unit.is_verified and full.admin_unit.name == "Meine Crew"
    assert full.event_place.name == "Rathaus"
    assert full.event_place.location.city == "Goslar"
    assert full.event_place.location.coordinate
    assert full.organizer.name == "Meine Crew"
    assert full.photo.license.code == "CC BY 4.0"
    assert full.photo.copyright_text == "EventCally"
    assert [c.name for c in full.categories][0] == "Other"
    assert len(full.categories) == 2
    assert full.custom_categories[0].category_set.label_or_name
    assert [d.start.year for d in full.date_definitions] == [2040, 2040]
    assert full.min_start_definition.start < full.date_definitions[1].start
    assert full.internal_tags == "secret,inhouse"
    assert full.rating == 80
    assert full.is_recurring is False
    assert full.category.name == "Other"
    assert list(full.custom_categories_by_set) == [1]


def test_recurring_event_is_flagged(read_repo, world):
    page = _search(read_repo, keyword="Jam")

    assert page.items[0].is_recurring is True


def test_search_runs_a_bounded_number_of_statements(app, db, read_repo, world):
    statements = []

    def count(conn, cursor, statement, *args):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    with app.app_context():
        engine = db.engine

    sa_event.listen(engine, "before_cursor_execute", count)
    try:
        _search(read_repo, method="search_event_dates")
    finally:
        sa_event.remove(engine, "before_cursor_execute", count)

    assert len(statements) <= 10


def test_list_events_for_search_pages_internally(read_repo, world, monkeypatch):
    from project.infrastructure.read_repositories import (
        sql_alchemy_event_search_read_repository as module,
    )

    monkeypatch.setattr(module, "_LOAD_CHUNK", 2)

    items = read_repo("list_events_for_search", EventSearchCriteria(), False, False)

    assert [item.name for item in items] == PUBLIC


def test_list_events_public_and_per_organization(read_repo, world):
    def names(query, private=False):
        page = read_repo("list_events", query, private)
        return [item.name for item in page.items]

    assert names(ListEventsQuery()) == PUBLIC
    assert names(ListEventsQuery(admin_unit_id=world["a"])) == [
        "Past Event",
        "Full Event",
        "Weekly Jam",
        "Allday Fest",
        "Cancelled Event",
    ]
    assert "Draft Event" in names(ListEventsQuery(admin_unit_id=world["a"]), True)
    assert names(ListEventsQuery(admin_unit_id=world["c"])) == []
    assert names(ListEventsQuery(admin_unit_id=world["c"]), True) == [
        "Unverified Event"
    ]
    assert names(ListEventsQuery(sort=TrackableSort.created_at_desc))[0] == (
        "Other Event"
    )
    assert read_repo("organization_exists", world["a"]) is True
    assert read_repo("organization_exists", 4711) is False


def test_list_event_dates_are_public_dates(read_repo, world):
    page = read_repo("list_event_dates", ListEventDatesQuery(page=PageRequest()))

    assert page.total == 9
    assert [item.start for item in page.items] == sorted(
        item.start for item in page.items
    )

    bounded = read_repo(
        "list_event_dates",
        ListEventDatesQuery(
            trackable=TrackableCriteria(created_at_from=datetime(2026, 1, 9))
        ),
    )
    assert 0 < bounded.total < page.total


def test_name_and_recurrence_criteria_of_the_manage_list(read_repo, world):
    assert _names(_search(read_repo, name="jam")) == ["Weekly Jam"]
    assert _names(_search(read_repo, name="^Full")) == ["Full Event"]
    assert _names(_search(read_repo, name="=Full")) == []
    assert _names(_search(read_repo, is_recurring=True)) == ["Weekly Jam"]
    assert _names(_search(read_repo, is_recurring=False)) == [
        n for n in PUBLIC if n != "Weekly Jam"
    ]


def test_counts_are_only_loaded_on_request(read_repo, world, seeder):
    seeder.create_reference_request(world["full"], world["b"])

    without = _search(read_repo, keyword="Full").items[0]
    with_counts = read_repo(
        "search_events",
        EventSearchCriteria(keyword="Full"),
        PageRequest(),
        False,
        False,
        None,
        True,
    ).items[0]

    assert without.number_of_dates is None
    assert with_counts.number_of_dates == 2
    assert with_counts.number_of_references == 0
    assert with_counts.number_of_reference_requests == 1


def test_events_know_whether_they_have_multiple_dates(read_repo, world):
    by_name = {item.name: item for item in _search(read_repo).items}

    assert by_name["Full Event"].has_multiple_dates() is True  # two definitions
    assert by_name["Weekly Jam"].has_multiple_dates() is True  # recurring
    assert by_name["Allday Fest"].has_multiple_dates() is False
