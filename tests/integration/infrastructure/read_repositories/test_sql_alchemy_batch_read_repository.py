"""SqlAlchemyBatchReadRepository and SqlAlchemyImageReadRepository against the
database, on the read session."""

import datetime

import pytest
from sqlalchemy import text

from project.application.queries import (
    ListDumpEventReferencesQuery,
    ListDumpEventsQuery,
    ListDumpOrganizationsQuery,
    ListDumpOrganizersQuery,
    ListDumpPlacesQuery,
)
from tests.integration.event_read_seed import seed_event_world


@pytest.fixture
def world(app, db, seeder):
    return seed_event_world(app, db, seeder)


def _repo_call(app, repo_name, method, *args):
    with app.app_context():
        repo = getattr(app.container.read_repos, repo_name)()

        with app.container.infrastructure.read_session_scope():
            return getattr(repo, method)(*args)


@pytest.fixture
def batch(app, db):
    return lambda method, *args: _repo_call(app, "batch_read_repo", method, *args)


@pytest.fixture
def images(app, db):
    return lambda method, *args: _repo_call(app, "image_read_repo", method, *args)


def test_public_dump_events_are_published_and_verified(batch, world):
    events = batch("list_dump_events", ListDumpEventsQuery(public_only=True))

    assert [e.name for e in events] == [
        "Full Event",
        "Weekly Jam",
        "Allday Fest",
        "Cancelled Event",
        "Past Event",
        "Other Event",
    ]
    assert events[0].co_organizers and events[0].photo and events[0].categories


def test_organization_dump_events_include_everything_of_it(batch, world):
    events = batch("list_dump_events", ListDumpEventsQuery(admin_unit_id=world["a"]))

    assert {e.name for e in events} >= {"Draft Event", "Planned Event"}
    assert "Other Event" not in {e.name for e in events}


def test_events_are_keyset_paged_by_id(batch, world):
    first = batch("list_dump_events", ListDumpEventsQuery(limit=3))
    second = batch(
        "list_dump_events", ListDumpEventsQuery(limit=3, after_id=first[-1].id)
    )

    assert [e.id for e in first] == [1, 2, 3]
    assert [e.id for e in second] == [4, 5, 6]
    assert batch("list_dump_events", ListDumpEventsQuery(after_id=999)) == []


def test_dump_places_organizers_organizations_and_references(batch, world):
    places = batch("list_dump_places", ListDumpPlacesQuery(admin_unit_id=world["a"]))
    organizers = batch(
        "list_dump_organizers", ListDumpOrganizersQuery(admin_unit_id=world["a"])
    )
    organizations = batch("list_dump_organizations", ListDumpOrganizationsQuery())
    references = batch("list_dump_event_references", ListDumpEventReferencesQuery())

    assert "Rathaus" in {p.name for p in places}
    assert {p.admin_unit_id for p in places} == {world["a"]}
    assert places[0].id < places[-1].id
    assert {o.admin_unit_id for o in organizers} == {world["a"]}
    assert [o.name for o in organizations][:2] == ["Meine Crew", "eventcally"]
    assert organizations[0].is_verified
    assert [(r.event_id, r.admin_unit_id) for r in references] == [
        (world["other"], world["a"])
    ]
    assert len(batch("list_dump_event_categories")) > 10


def test_single_organization_dump(batch, world):
    (organization,) = batch(
        "list_dump_organizations", ListDumpOrganizationsQuery(admin_unit_id=world["b"])
    )

    assert organization.name == "Other Crew"


def test_sitemap_lists_upcoming_public_events(batch, world):
    events = batch("list_sitemap_events")

    assert [e.id for e in events] == [
        world["full"],
        world["recurring"],
        world["allday"],
        world["cancelled"],
        world["other"],
    ]
    assert all(e.last_modified_at for e in events)


def _age(app, db, statement, days, **params):
    with app.app_context():
        db.session.execute(
            text(statement),
            {
                "when": datetime.datetime.now(datetime.UTC)
                - datetime.timedelta(days=days)
            }
            | params,
        )
        db.session.commit()


def test_due_deletions(app, db, batch, world):
    _age(
        app,
        db,
        "UPDATE adminunit SET deletion_requested_at = :when WHERE id = :id",
        4,
        id=world["b"],
    )
    _age(
        app,
        db,
        "UPDATE adminunit SET deletion_requested_at = :when WHERE id = :id",
        1,
        id=world["c"],
    )
    _age(app, db, 'UPDATE "user" SET deletion_requested_at = :when WHERE id = 1', 4)

    assert batch("list_organization_ids_due_for_deletion") == [world["b"]]
    assert batch("list_user_ids_due_for_deletion") == [1]


def test_ghost_users_never_confirmed_for_a_month(app, db, batch, seeder, world):
    ghost_id = seeder.create_user("ghost@test.de", confirm=False)

    assert batch("list_ghost_user_ids") == []

    _age(
        app, db, 'UPDATE "user" SET created_at = :when WHERE id = :id', 40, id=ghost_id
    )
    assert batch("list_ghost_user_ids") == [ghost_id]


def test_old_events_ended_and_untouched_for_a_year(app, db, batch, world):
    assert batch("list_old_event_ids") == []

    _age(
        app,
        db,
        "UPDATE event SET updated_at = :when WHERE id = :id",
        400,
        id=world["past"],
    )
    # The past event ended in 2020, so it is old once untouched for a year.
    assert batch("list_old_event_ids") == [world["past"]]


def test_recurring_events(app, db, seeder, batch):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    first = seeder.create_event(
        admin_unit_id, recurrence_rule="RRULE:FREQ=DAILY;COUNT=7"
    )
    seeder.create_event(admin_unit_id, recurrence_rule=None)
    seeder.create_event(admin_unit_id, recurrence_rule="")
    second = seeder.create_event(
        admin_unit_id, recurrence_rule="RRULE:FREQ=WEEKLY;COUNT=2"
    )

    assert batch("list_recurring_event_ids") == [first, second]


def test_image_meta_and_file(app, db, seeder, images):
    image_id = seeder.upsert_default_image()

    meta = images("get_meta", image_id)
    image_file = images("get_file", image_id)

    assert meta.get_file_extension() == "png"
    assert meta.get_hash() > 0
    assert image_file.data and image_file.get_file_extension() == "png"
    assert images("get_meta", 4711) is None
    assert images("get_file", 4711) is None


def test_image_without_format_or_timestamps_falls_back(app, db, seeder, images):
    image_id = seeder.upsert_default_image()

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE image SET encoding_format = NULL, created_at = NULL,"
                " updated_at = NULL WHERE id = :id"
            ),
            {"id": image_id},
        )
        db.session.commit()

    meta = images("get_meta", image_id)

    assert meta.get_file_extension() == "png"
    assert meta.get_hash() == 0
    assert images("get_file", image_id).get_file_extension() == "png"
