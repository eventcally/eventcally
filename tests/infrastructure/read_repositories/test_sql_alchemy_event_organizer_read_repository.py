"""SqlAlchemyEventOrganizerReadRepository against the database, on the read session."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import text

from project.application.queries import (
    EventOrganizerSort,
    ListEventOrganizersQuery,
    LookupEventOrganizersQuery,
    PageRequest,
    TrackableCriteria,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.event_organizer_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def _set_trackable(app, db, organizer_id, created_at, updated_at=None):
    with app.app_context():
        db.session.execute(
            text(
                "UPDATE eventorganizer"
                " SET created_at = :created_at, updated_at = :updated_at"
                " WHERE id = :id"
            ),
            {"id": organizer_id, "created_at": created_at, "updated_at": updated_at},
        )
        db.session.commit()


@pytest.fixture
def organizers(app, db, seeder):
    """Organization "Meine Crew" with five organizers and fixed timestamps."""
    _, admin_unit_id = seeder.setup_base(log_in=False)
    ids = {
        "meine_crew": seeder.upsert_default_event_organizer(admin_unit_id),
        "alpha": seeder.upsert_event_organizer(admin_unit_id, "Alpha"),
        "lake": seeder.upsert_event_organizer(admin_unit_id, "crew am See"),
        "central": seeder.upsert_event_organizer(admin_unit_id, "Zentrale Crew"),
        "bravo": seeder.upsert_event_organizer(admin_unit_id, "Bravo"),
    }
    _set_trackable(
        app, db, ids["meine_crew"], datetime(2026, 1, 1), datetime(2026, 3, 1)
    )
    _set_trackable(app, db, ids["alpha"], datetime(2026, 2, 1))
    _set_trackable(app, db, ids["lake"], datetime(2026, 1, 15), datetime(2026, 2, 20))
    _set_trackable(app, db, ids["central"], datetime(2026, 1, 10))
    _set_trackable(app, db, ids["bravo"], datetime(2026, 3, 5))

    _, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Andere Crew", log_in=False
    )
    seeder.upsert_event_organizer(other_admin_unit_id, "Crew B")

    return admin_unit_id, other_admin_unit_id, ids


def _names(page):
    return [item.name for item in page.items]


def _list(read_repo, admin_unit_id, **kwargs):
    return read_repo(
        "list", ListEventOrganizersQuery(admin_unit_id=admin_unit_id, **kwargs)
    )


def test_organization_exists(read_repo, organizers):
    admin_unit_id, _, _ = organizers

    assert read_repo("organization_exists", admin_unit_id) is True
    assert read_repo("organization_exists", 4711) is False


def test_list_is_scoped_to_organization_and_sorted_by_name(read_repo, organizers):
    admin_unit_id, other_admin_unit_id, _ = organizers

    page = _list(read_repo, admin_unit_id)

    assert _names(page) == [
        "Alpha",
        "Bravo",
        "crew am See",
        "Meine Crew",
        "Zentrale Crew",
    ]
    assert page.total == 5
    assert "Crew B" in _names(_list(read_repo, other_admin_unit_id))


def test_name_ranks_prefix_matches_first(read_repo, organizers):
    admin_unit_id, _, _ = organizers

    page = _list(read_repo, admin_unit_id, name="crew")

    assert _names(page) == ["crew am See", "Meine Crew", "Zentrale Crew"]


def test_name_ranking_comes_after_trackable_sort(read_repo, organizers):
    admin_unit_id, _, _ = organizers

    page = _list(
        read_repo, admin_unit_id, name="crew", sort=EventOrganizerSort.created_at_desc
    )

    assert _names(page) == ["crew am See", "Zentrale Crew", "Meine Crew"]


@pytest.mark.parametrize(
    "keyword, expected",
    [
        ("crew", ["crew am See", "Meine Crew", "Zentrale Crew"]),
        ("^crew", ["crew am See"]),
        ("=alpha", ["Alpha"]),
        ("RAV", ["Bravo"]),
    ],
)
def test_keyword_uses_like_term_syntax(read_repo, organizers, keyword, expected):
    admin_unit_id, _, _ = organizers

    assert _names(_list(read_repo, admin_unit_id, keyword=keyword)) == expected


@pytest.mark.parametrize(
    "sort, expected",
    [
        (
            EventOrganizerSort.name,
            ["Alpha", "Bravo", "crew am See", "Meine Crew", "Zentrale Crew"],
        ),
        (
            EventOrganizerSort.created_at_desc,
            ["Bravo", "Alpha", "crew am See", "Zentrale Crew", "Meine Crew"],
        ),
        (
            # Never-updated organizers last, then by name.
            EventOrganizerSort.updated_at_desc,
            ["Meine Crew", "crew am See", "Alpha", "Bravo", "Zentrale Crew"],
        ),
        (
            EventOrganizerSort.last_modified_at_desc,
            ["Bravo", "Meine Crew", "crew am See", "Alpha", "Zentrale Crew"],
        ),
    ],
)
def test_sort(read_repo, organizers, sort, expected):
    admin_unit_id, _, _ = organizers

    assert _names(_list(read_repo, admin_unit_id, sort=sort)) == expected


def test_sort_by_number_of_events(app, db, seeder, read_repo, organizers):
    admin_unit_id, _, ids = organizers
    event_ids = [seeder.create_event(admin_unit_id) for _ in range(3)]

    with app.app_context():
        db.session.execute(
            text("UPDATE event SET organizer_id = :organizer_id WHERE id IN :ids"),
            {"organizer_id": ids["bravo"], "ids": tuple(event_ids[:2])},
        )
        db.session.commit()

    page = _list(
        read_repo, admin_unit_id, sort=EventOrganizerSort.number_of_events_desc
    )

    assert [(item.name, item.number_of_events) for item in page.items] == [
        ("Bravo", 2),
        ("Meine Crew", 1),
        ("Alpha", 0),
        ("crew am See", 0),
        ("Zentrale Crew", 0),
    ]


@pytest.mark.parametrize(
    "criteria, expected",
    [
        ({"created_at_from": datetime(2026, 2, 1)}, ["Alpha", "Bravo"]),
        (
            {"created_at_to": datetime(2026, 1, 15)},
            ["Meine Crew", "Zentrale Crew"],
        ),
        ({"updated_at_from": datetime(2026, 2, 21)}, ["Meine Crew"]),
        ({"updated_at_to": datetime(2026, 3, 1)}, ["crew am See"]),
        (
            {"last_modified_at_from": datetime(2026, 3, 1)},
            ["Bravo", "Meine Crew"],
        ),
        (
            {"last_modified_at_to": datetime(2026, 2, 1)},
            ["Zentrale Crew"],
        ),
    ],
)
def test_trackable_bounds(read_repo, organizers, criteria, expected):
    admin_unit_id, _, _ = organizers

    page = _list(read_repo, admin_unit_id, trackable=TrackableCriteria(**criteria))

    assert _names(page) == expected


def test_created_at_to_does_not_bound_last_modified_at(read_repo, organizers):
    """Regression: TrackableSearchParams defaulted last_modified_at_to to created_at_to."""
    admin_unit_id, _, _ = organizers

    page = _list(
        read_repo,
        admin_unit_id,
        trackable=TrackableCriteria(created_at_to=datetime(2026, 1, 20)),
    )

    # Meine Crew and crew am See were updated after the bound, and still match.
    assert _names(page) == ["crew am See", "Meine Crew", "Zentrale Crew"]


def test_pagination(read_repo, organizers):
    admin_unit_id, _, _ = organizers

    page = _list(read_repo, admin_unit_id, page=PageRequest(page=2, per_page=2))

    assert _names(page) == ["crew am See", "Meine Crew"]
    assert (page.page, page.per_page, page.total, page.pages) == (2, 2, 5, 3)
    assert page.has_prev and page.has_next

    last = _list(read_repo, admin_unit_id, page=PageRequest(page=3, per_page=2))
    assert _names(last) == ["Zentrale Crew"]
    assert not last.has_next

    beyond = _list(read_repo, admin_unit_id, page=PageRequest(page=4, per_page=2))
    assert beyond.items == [] and beyond.is_out_of_range


def test_list_item_fields(app, db, seeder, read_repo, organizers):
    admin_unit_id, _, ids = organizers
    image_id = seeder.upsert_default_image()

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE eventorganizer SET logo_id = :image_id, phone = '123'"
                " WHERE id = :id"
            ),
            {"id": ids["alpha"], "image_id": image_id},
        )
        db.session.commit()

    items = {item.name: item for item in _list(read_repo, admin_unit_id).items}

    assert items["Alpha"].has_logo is True
    assert items["Alpha"].phone == "123"
    assert items["Alpha"].last_modified_at == datetime(2026, 2, 1)
    assert items["Bravo"].has_logo is False
    assert items["Meine Crew"].last_modified_at == datetime(2026, 3, 1)


def test_get_with_location_logo_and_license(app, db, seeder, read_repo, organizers):
    admin_unit_id, _, ids = organizers
    image_id = seeder.upsert_default_image()

    with app.app_context():
        from project.models import EventOrganizer, Location

        organizer = db.session.get(EventOrganizer, ids["alpha"])
        organizer.url = "https://example.com"
        organizer.location = Location(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            latitude="51.9077888",
            longitude="10.4333312",
        )
        organizer.logo_id = image_id
        db.session.commit()

        db.session.execute(
            text(
                "UPDATE image SET copyright_text = 'EventCally', license_id = 2,"
                " created_at = :created_at, updated_at = NULL WHERE id = :id"
            ),
            {"id": image_id, "created_at": datetime(2026, 1, 2, 8, 30)},
        )
        db.session.commit()

    detail = read_repo("get", ids["alpha"])

    assert detail.name == "Alpha"
    assert detail.url == "https://example.com"
    assert detail.admin_unit.id == admin_unit_id
    assert detail.admin_unit.name == "Meine Crew"
    assert detail.location.postalCode == "38640"
    assert detail.location.latitude == Decimal("51.9077888000000000")
    assert detail.logo.id == image_id
    assert detail.logo.copyright_text == "EventCally"
    assert detail.logo.get_hash() == 1767342600000
    assert detail.logo.license.code == "CC BY 4.0"


def test_get_logo_without_license(app, db, seeder, read_repo, organizers):
    _, _, ids = organizers
    image_id = seeder.upsert_default_image()

    with app.app_context():
        db.session.execute(
            text("UPDATE eventorganizer SET logo_id = :image_id WHERE id = :id"),
            {"id": ids["bravo"], "image_id": image_id},
        )
        db.session.commit()

    detail = read_repo("get", ids["bravo"])

    assert detail.logo.id == image_id
    assert detail.logo.license is None


def test_get_bare(read_repo, organizers):
    _, _, ids = organizers

    detail = read_repo("get", ids["bravo"])

    assert detail.location is None
    assert detail.logo is None
    assert detail.created_at == datetime(2026, 3, 5)
    assert detail.updated_at is None


def test_get_unknown(read_repo, organizers):
    assert read_repo("get", 4711) is None


@pytest.mark.parametrize(
    "name, exclude, expected",
    [
        ("alpha", None, True),
        ("ALPHA", None, True),
        ("Alpha", "alpha", False),
        ("Alpha", "bravo", True),
        ("Alphabet", None, False),
        ("Crew B", None, False),
    ],
)
def test_is_name_taken(read_repo, organizers, name, exclude, expected):
    admin_unit_id, _, ids = organizers
    exclude_id = ids[exclude] if exclude else None

    assert read_repo("is_name_taken", admin_unit_id, name, exclude_id) is expected


def test_is_name_taken_for_unknown_organization(read_repo, organizers):
    assert read_repo("is_name_taken", -1, "Alpha") is False


def _count_selects(app, db, call):
    from sqlalchemy import event

    statements = []

    def listener(conn, cursor, statement, *args):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    with app.app_context():
        engine = db.engine
    event.listen(engine, "before_cursor_execute", listener)
    try:
        result = call()
    finally:
        event.remove(engine, "before_cursor_execute", listener)

    return result, len(statements)


def test_get_for_edit_with_location_logo_and_license(
    app, db, seeder, read_repo, organizers
):
    admin_unit_id, _, ids = organizers
    image_id = seeder.upsert_default_image()

    with app.app_context():
        from project.models import EventOrganizer, Image, Location

        organizer = db.session.get(EventOrganizer, ids["alpha"])
        organizer.url = "https://example.com"
        organizer.email = "info@example.com"
        organizer.phone = "123"
        organizer.fax = "456"
        organizer.location = Location(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            latitude="51.9077888",
            longitude="10.4333312",
        )
        organizer.logo_id = image_id
        db.session.commit()
        db.session.execute(
            text(
                "UPDATE image SET copyright_text = 'EventCally', license_id = 2"
                " WHERE id = :id"
            ),
            {"id": image_id},
        )
        db.session.commit()
        image_data = db.session.get(Image, image_id).data

    edit, selects = _count_selects(
        app, db, lambda: read_repo("get_for_edit", ids["alpha"])
    )

    assert selects == 1
    assert edit.id == ids["alpha"]
    assert edit.admin_unit_id == admin_unit_id
    assert edit.name == "Alpha"
    assert edit.url == "https://example.com"
    assert edit.email == "info@example.com"
    assert edit.phone == "123"
    assert edit.fax == "456"
    assert edit.location.city == "Goslar"
    assert edit.location.latitude == Decimal("51.9077888000000000")
    assert edit.logo.id == image_id
    assert edit.logo.data == image_data
    assert edit.logo.encoding_format == "image/png"
    assert edit.logo.copyright_text == "EventCally"
    assert edit.logo.license.code == "CC BY 4.0"
    assert edit.logo.license.name


def test_get_for_edit_logo_without_license(app, db, seeder, read_repo, organizers):
    _, _, ids = organizers
    image_id = seeder.upsert_default_image()

    with app.app_context():
        db.session.execute(
            text("UPDATE eventorganizer SET logo_id = :image_id WHERE id = :id"),
            {"id": ids["bravo"], "image_id": image_id},
        )
        db.session.commit()

    edit = read_repo("get_for_edit", ids["bravo"])

    assert edit.logo.data
    assert edit.logo.license is None


def test_get_for_edit_bare(app, db, read_repo, organizers):
    _, _, ids = organizers

    with app.app_context():
        db.session.execute(
            text("UPDATE eventorganizer SET location_id = NULL WHERE id = :id"),
            {"id": ids["bravo"]},
        )
        db.session.commit()

    edit = read_repo("get_for_edit", ids["bravo"])

    assert edit.name == "Bravo"
    assert edit.location is None
    assert edit.logo is None


def test_get_for_edit_unknown(read_repo, organizers):
    assert read_repo("get_for_edit", 4711) is None


def _lookup(read_repo, admin_unit_id, **kwargs):
    return read_repo(
        "lookup", LookupEventOrganizersQuery(admin_unit_id=admin_unit_id, **kwargs)
    )


def test_lookup_is_scoped_and_sorted_by_lower_name(read_repo, organizers):
    admin_unit_id, _, _ = organizers

    page = _lookup(read_repo, admin_unit_id)

    assert _names(page) == [
        "Alpha",
        "Bravo",
        "crew am See",
        "Meine Crew",
        "Zentrale Crew",
    ]
    assert page.total == 5


def test_lookup_term_matches_anywhere_and_pages(read_repo, organizers):
    admin_unit_id, _, _ = organizers

    page = _lookup(read_repo, admin_unit_id, term="crew")
    assert _names(page) == ["crew am See", "Meine Crew", "Zentrale Crew"]

    page = _lookup(read_repo, admin_unit_id, page=PageRequest(page=2, per_page=2))
    assert _names(page) == ["crew am See", "Meine Crew"]
    assert page.has_next


def test_get_ref_only_within_the_organization(read_repo, organizers):
    admin_unit_id, other_admin_unit_id, ids = organizers

    ref = read_repo("get_ref", admin_unit_id, ids["alpha"])

    assert (ref.id, ref.name) == (ids["alpha"], "Alpha")
    assert read_repo("get_ref", other_admin_unit_id, ids["alpha"]) is None
    assert read_repo("get_ref", admin_unit_id, 4711) is None
