"""SqlAlchemyEventPlaceReadRepository against the database, on the read session."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import text

from project.application.queries import (
    EventPlaceSort,
    ListEventPlacesQuery,
    ListEventPlaceSuggestionsQuery,
    LookupEventPlacesQuery,
    PageRequest,
    TrackableCriteria,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.event_place_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def _set_trackable(app, db, place_id, created_at, updated_at=None):
    with app.app_context():
        db.session.execute(
            text(
                "UPDATE eventplace"
                " SET created_at = :created_at, updated_at = :updated_at"
                " WHERE id = :id"
            ),
            {"id": place_id, "created_at": created_at, "updated_at": updated_at},
        )
        db.session.commit()


def _delete_base_places(app, db, keep_admin_unit_id=None):
    """`setup_base` seeds a "City" place per organization; the tests control all names."""
    with app.app_context():
        db.session.execute(
            text(
                "DELETE FROM eventplace WHERE name = 'City' AND admin_unit_id != :keep"
            ),
            {"keep": keep_admin_unit_id or -1},
        )
        db.session.commit()


@pytest.fixture
def places(app, db, seeder):
    """Organization "Meine Crew" with five places and fixed timestamps."""
    _, admin_unit_id = seeder.setup_base(log_in=False)
    _delete_base_places(app, db)
    ids = {
        "stadthalle": seeder.upsert_event_place(admin_unit_id, "Stadthalle"),
        "alpha": seeder.upsert_event_place(admin_unit_id, "Alpha"),
        "lake": seeder.upsert_event_place(admin_unit_id, "halle am See"),
        "central": seeder.upsert_event_place(admin_unit_id, "Zentrale Halle"),
        "bravo": seeder.upsert_event_place(admin_unit_id, "Bravo"),
    }
    _set_trackable(
        app, db, ids["stadthalle"], datetime(2026, 1, 1), datetime(2026, 3, 1)
    )
    _set_trackable(app, db, ids["alpha"], datetime(2026, 2, 1))
    _set_trackable(app, db, ids["lake"], datetime(2026, 1, 15), datetime(2026, 2, 20))
    _set_trackable(app, db, ids["central"], datetime(2026, 1, 10))
    _set_trackable(app, db, ids["bravo"], datetime(2026, 3, 5))

    _, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Andere Crew", log_in=False
    )
    _delete_base_places(app, db, keep_admin_unit_id=admin_unit_id)
    seeder.upsert_event_place(other_admin_unit_id, "Halle B")

    return admin_unit_id, other_admin_unit_id, ids


def _names(page):
    return [item.name for item in page.items]


def _list(read_repo, admin_unit_id, **kwargs):
    return read_repo(
        "list", ListEventPlacesQuery(admin_unit_id=admin_unit_id, **kwargs)
    )


def _suggest(read_repo, admin_unit_id, **kwargs):
    result = read_repo(
        "list_suggestions",
        ListEventPlaceSuggestionsQuery(admin_unit_id=admin_unit_id, **kwargs),
    )
    return [item.name for item in result]


def test_organization_exists(read_repo, places):
    admin_unit_id, _, _ = places

    assert read_repo("organization_exists", admin_unit_id) is True
    assert read_repo("organization_exists", 4711) is False


def test_list_is_scoped_to_organization_and_sorted_by_name(read_repo, places):
    admin_unit_id, other_admin_unit_id, _ = places

    page = _list(read_repo, admin_unit_id)

    assert _names(page) == [
        "Alpha",
        "Bravo",
        "halle am See",
        "Stadthalle",
        "Zentrale Halle",
    ]
    assert page.total == 5
    assert "Halle B" in _names(_list(read_repo, other_admin_unit_id))


def test_name_matches_anywhere_without_prefix_ranking(read_repo, places):
    admin_unit_id, _, _ = places

    page = _list(read_repo, admin_unit_id, name="halle")

    assert _names(page) == ["halle am See", "Stadthalle", "Zentrale Halle"]


def test_name_filter_follows_trackable_sort(read_repo, places):
    admin_unit_id, _, _ = places

    page = _list(
        read_repo, admin_unit_id, name="Halle", sort=EventPlaceSort.created_at_desc
    )

    assert _names(page) == ["halle am See", "Zentrale Halle", "Stadthalle"]


@pytest.mark.parametrize(
    "keyword, expected",
    [
        ("halle", ["halle am See", "Stadthalle", "Zentrale Halle"]),
        ("^halle", ["halle am See"]),
        ("=alpha", ["Alpha"]),
        ("RAV", ["Bravo"]),
    ],
)
def test_keyword_uses_like_term_syntax(read_repo, places, keyword, expected):
    admin_unit_id, _, _ = places

    assert _names(_list(read_repo, admin_unit_id, keyword=keyword)) == expected


@pytest.mark.parametrize(
    "sort, expected",
    [
        (
            EventPlaceSort.name,
            ["Alpha", "Bravo", "halle am See", "Stadthalle", "Zentrale Halle"],
        ),
        (
            EventPlaceSort.created_at_desc,
            ["Bravo", "Alpha", "halle am See", "Zentrale Halle", "Stadthalle"],
        ),
        (
            # Never-updated places last, then by name.
            EventPlaceSort.updated_at_desc,
            ["Stadthalle", "halle am See", "Alpha", "Bravo", "Zentrale Halle"],
        ),
        (
            EventPlaceSort.last_modified_at_desc,
            ["Bravo", "Stadthalle", "halle am See", "Alpha", "Zentrale Halle"],
        ),
    ],
)
def test_sort(read_repo, places, sort, expected):
    admin_unit_id, _, _ = places

    assert _names(_list(read_repo, admin_unit_id, sort=sort)) == expected


def test_sort_by_number_of_events(app, db, seeder, read_repo, places):
    admin_unit_id, _, ids = places
    event_ids = [seeder.create_event(admin_unit_id) for _ in range(3)]

    with app.app_context():
        db.session.execute(
            text("UPDATE event SET event_place_id = :place_id WHERE id IN :ids"),
            {"place_id": ids["bravo"], "ids": tuple(event_ids[:2])},
        )
        db.session.execute(
            text("UPDATE event SET event_place_id = :place_id WHERE id = :id"),
            {"place_id": ids["alpha"], "id": event_ids[2]},
        )
        # `create_event` seeds a default place, now unreferenced.
        db.session.execute(
            text(
                "DELETE FROM eventplace WHERE name = 'Meine Crew' AND admin_unit_id = :id"
            ),
            {"id": admin_unit_id},
        )
        db.session.commit()

    page = _list(read_repo, admin_unit_id, sort=EventPlaceSort.number_of_events_desc)

    assert [(item.name, item.number_of_events) for item in page.items] == [
        ("Bravo", 2),
        ("Alpha", 1),
        ("halle am See", 0),
        ("Stadthalle", 0),
        ("Zentrale Halle", 0),
    ]


@pytest.mark.parametrize(
    "criteria, expected",
    [
        ({"created_at_from": datetime(2026, 2, 1)}, ["Alpha", "Bravo"]),
        (
            {"created_at_to": datetime(2026, 1, 15)},
            ["Stadthalle", "Zentrale Halle"],
        ),
        ({"updated_at_from": datetime(2026, 2, 21)}, ["Stadthalle"]),
        ({"updated_at_to": datetime(2026, 3, 1)}, ["halle am See"]),
        (
            {"last_modified_at_from": datetime(2026, 3, 1)},
            ["Bravo", "Stadthalle"],
        ),
        (
            {"last_modified_at_to": datetime(2026, 2, 1)},
            ["Zentrale Halle"],
        ),
    ],
)
def test_trackable_bounds(read_repo, places, criteria, expected):
    admin_unit_id, _, _ = places

    page = _list(read_repo, admin_unit_id, trackable=TrackableCriteria(**criteria))

    assert _names(page) == expected


def test_created_at_to_does_not_bound_last_modified_at(read_repo, places):
    """Regression: TrackableSearchParams defaulted last_modified_at_to to created_at_to."""
    admin_unit_id, _, _ = places

    page = _list(
        read_repo,
        admin_unit_id,
        trackable=TrackableCriteria(created_at_to=datetime(2026, 1, 20)),
    )

    # Stadthalle and halle am See were updated after the bound, and still match.
    assert _names(page) == ["halle am See", "Stadthalle", "Zentrale Halle"]


def test_pagination(read_repo, places):
    admin_unit_id, _, _ = places

    page = _list(read_repo, admin_unit_id, page=PageRequest(page=2, per_page=2))

    assert _names(page) == ["halle am See", "Stadthalle"]
    assert (page.page, page.per_page, page.total, page.pages) == (2, 2, 5, 3)
    assert page.has_prev and page.has_next

    last = _list(read_repo, admin_unit_id, page=PageRequest(page=3, per_page=2))
    assert _names(last) == ["Zentrale Halle"]
    assert not last.has_next

    beyond = _list(read_repo, admin_unit_id, page=PageRequest(page=4, per_page=2))
    assert beyond.items == [] and beyond.is_out_of_range


def test_list_item_photo_and_coordinates(app, db, seeder, read_repo, places):
    admin_unit_id, _, ids = places
    image_id = seeder.upsert_default_image()

    with app.app_context():
        from project.models import EventPlace, Location

        stadthalle = db.session.get(EventPlace, ids["stadthalle"])
        stadthalle.location = Location(
            city="Goslar", latitude="51.9077888", longitude="10.4333312"
        )
        stadthalle.photo_id = image_id
        central = db.session.get(EventPlace, ids["central"])
        central.location = Location(city="Hamburg")
        db.session.commit()

    items = {item.name: item for item in _list(read_repo, admin_unit_id).items}

    assert items["Stadthalle"].has_photo is True
    assert items["Stadthalle"].has_coordinates is True
    assert items["Stadthalle"].location.city == "Goslar"
    assert items["Zentrale Halle"].has_photo is False
    assert items["Zentrale Halle"].has_coordinates is False
    assert items["Zentrale Halle"].location.city == "Hamburg"
    assert items["Bravo"].has_photo is False
    assert items["Bravo"].has_coordinates is False
    assert items["Bravo"].location is None
    assert items["Alpha"].last_modified_at == datetime(2026, 2, 1)


def test_get_with_location_photo_and_license(app, db, seeder, read_repo, places):
    admin_unit_id, _, ids = places
    image_id = seeder.upsert_default_image()

    with app.app_context():
        from project.models import EventPlace, Location

        place = db.session.get(EventPlace, ids["alpha"])
        place.url = "https://example.com"
        place.description = "Die große Halle"
        place.location = Location(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            latitude="51.9077888",
            longitude="10.4333312",
        )
        place.photo_id = image_id
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
    assert detail.description == "Die große Halle"
    assert detail.admin_unit.id == admin_unit_id
    assert detail.admin_unit.name == "Meine Crew"
    assert detail.location.postalCode == "38640"
    assert detail.location.latitude == Decimal("51.9077888000000000")
    assert detail.photo.id == image_id
    assert detail.photo.copyright_text == "EventCally"
    assert detail.photo.get_hash() == 1767342600000
    assert detail.photo.license.code == "CC BY 4.0"


def test_get_photo_without_license(app, db, seeder, read_repo, places):
    _, _, ids = places
    image_id = seeder.upsert_default_image()

    with app.app_context():
        db.session.execute(
            text("UPDATE eventplace SET photo_id = :image_id WHERE id = :id"),
            {"id": ids["bravo"], "image_id": image_id},
        )
        db.session.commit()

    detail = read_repo("get", ids["bravo"])

    assert detail.photo.id == image_id
    assert detail.photo.license is None


def test_get_bare(read_repo, places):
    _, _, ids = places

    detail = read_repo("get", ids["bravo"])

    assert detail.location is None
    assert detail.photo is None
    assert detail.url is None
    assert detail.description is None
    assert detail.created_at == datetime(2026, 3, 5)
    assert detail.updated_at is None


def test_get_unknown(read_repo, places):
    assert read_repo("get", 4711) is None


@pytest.mark.parametrize(
    "name, exclude, expected",
    [
        ("alpha", None, True),
        ("ALPHA", None, True),
        ("Alpha", "alpha", False),
        ("Alpha", "bravo", True),
        ("Alphabet", None, False),
        ("Halle B", None, False),
    ],
)
def test_is_name_taken(read_repo, places, name, exclude, expected):
    admin_unit_id, _, ids = places
    exclude_id = ids[exclude] if exclude else None

    assert read_repo("is_name_taken", admin_unit_id, name, exclude_id) is expected


def test_is_name_taken_for_unknown_organization(read_repo, places):
    assert read_repo("is_name_taken", -1, "Alpha") is False


def test_suggestions_rank_prefix_matches_first(read_repo, places):
    admin_unit_id, _, _ = places

    assert _suggest(read_repo, admin_unit_id, keyword="halle") == [
        "halle am See",
        "Stadthalle",
        "Zentrale Halle",
    ]


def test_suggestions_without_keyword_are_sorted_by_name(read_repo, places):
    admin_unit_id, _, _ = places

    assert _suggest(read_repo, admin_unit_id) == [
        "Alpha",
        "Bravo",
        "halle am See",
        "Stadthalle",
        "Zentrale Halle",
    ]


def test_suggestions_are_limited_and_scoped(read_repo, places):
    admin_unit_id, other_admin_unit_id, _ = places

    assert _suggest(read_repo, admin_unit_id, limit=2) == ["Alpha", "Bravo"]
    assert _suggest(read_repo, other_admin_unit_id) == ["Halle B"]
    assert _suggest(read_repo, 4711, keyword="halle") == []


def test_suggestions_carry_location(app, db, read_repo, places):
    admin_unit_id, _, ids = places

    with app.app_context():
        from project.models import EventPlace, Location

        db.session.get(EventPlace, ids["alpha"]).location = Location(city="Goslar")
        db.session.commit()

    result = read_repo(
        "list_suggestions",
        ListEventPlaceSuggestionsQuery(admin_unit_id=admin_unit_id, keyword="alpha"),
    )

    assert [(item.name, item.location.city) for item in result] == [("Alpha", "Goslar")]


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


def test_get_for_edit_with_location_photo_and_license(
    app, db, seeder, read_repo, places
):
    admin_unit_id, _, ids = places
    image_id = seeder.upsert_default_image()

    with app.app_context():
        from project.models import EventPlace, Image, Location

        place = db.session.get(EventPlace, ids["alpha"])
        place.url = "https://example.com"
        place.description = "Die große Halle"
        place.location = Location(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            latitude="51.9077888",
            longitude="10.4333312",
        )
        place.photo_id = image_id
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
    assert edit.description == "Die große Halle"
    assert edit.location.city == "Goslar"
    assert edit.location.latitude == Decimal("51.9077888000000000")
    assert edit.photo.id == image_id
    assert edit.photo.data == image_data
    assert edit.photo.encoding_format == "image/png"
    assert edit.photo.copyright_text == "EventCally"
    assert edit.photo.license.code == "CC BY 4.0"
    assert edit.photo.license.name


def test_get_for_edit_photo_without_license(app, db, seeder, read_repo, places):
    _, _, ids = places
    image_id = seeder.upsert_default_image()

    with app.app_context():
        db.session.execute(
            text("UPDATE eventplace SET photo_id = :image_id WHERE id = :id"),
            {"id": ids["bravo"], "image_id": image_id},
        )
        db.session.commit()

    edit = read_repo("get_for_edit", ids["bravo"])

    assert edit.photo.data
    assert edit.photo.license is None


def test_get_for_edit_bare(app, db, read_repo, places):
    _, _, ids = places

    with app.app_context():
        db.session.execute(
            text("UPDATE eventplace SET location_id = NULL WHERE id = :id"),
            {"id": ids["bravo"]},
        )
        db.session.commit()

    edit = read_repo("get_for_edit", ids["bravo"])

    assert edit.name == "Bravo"
    assert edit.location is None
    assert edit.photo is None


def test_get_for_edit_unknown(read_repo, places):
    assert read_repo("get_for_edit", 4711) is None


def _lookup(read_repo, admin_unit_id, **kwargs):
    return read_repo(
        "lookup", LookupEventPlacesQuery(admin_unit_id=admin_unit_id, **kwargs)
    )


def test_lookup_is_scoped_filtered_and_paged(read_repo, places):
    admin_unit_id, _, _ = places

    page = _lookup(read_repo, admin_unit_id)
    assert _names(page) == [
        "Alpha",
        "Bravo",
        "halle am See",
        "Stadthalle",
        "Zentrale Halle",
    ]

    page = _lookup(read_repo, admin_unit_id, term="halle")
    assert _names(page) == ["halle am See", "Stadthalle", "Zentrale Halle"]

    page = _lookup(read_repo, admin_unit_id, page=PageRequest(page=3, per_page=2))
    assert _names(page) == ["Zentrale Halle"]
    assert not page.has_next


def test_get_ref_only_within_the_organization(read_repo, places):
    admin_unit_id, other_admin_unit_id, ids = places

    place_id = ids["alpha"]
    ref = read_repo("get_ref", admin_unit_id, place_id)

    assert ref.id == place_id
    assert read_repo("get_ref", other_admin_unit_id, place_id) is None
    assert read_repo("get_ref", admin_unit_id, 4711) is None
