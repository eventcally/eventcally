"""SqlAlchemyEventDetailReadRepository against the database, on the read session."""

import pytest
from sqlalchemy import event as sa_event

from project.application.queries import PageRequest
from project.domain.models.enums.event_public_status import EventPublicStatus
from tests.event_read_seed import seed_event_world


@pytest.fixture
def world(app, db, seeder):
    return seed_event_world(app, db, seeder)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.event_detail_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def test_visibility_facts(read_repo, world):
    published = read_repo("get_visibility", world["full"])
    draft = read_repo("get_visibility", world["draft"])
    unverified = read_repo("get_visibility", world["unverified"])

    assert published.public_status == EventPublicStatus.published
    assert published.admin_unit_id == world["a"] and published.admin_unit_is_verified
    assert draft.public_status == EventPublicStatus.draft
    assert unverified.admin_unit_is_verified is False
    assert read_repo("get_visibility", 4711) is None


def test_visibility_facts_of_a_date(read_repo, world):
    visibility = read_repo("get_visibility_of_date", 1)

    assert visibility.event_id == world["full"]
    assert read_repo("get_visibility_of_date", 4711) is None


def test_detail_has_everything_the_page_shows(read_repo, world):
    detail = read_repo("get_detail", world["full"], world["a"])

    assert detail.name == "Full Event"
    assert [o.name for o in detail.co_organizers] == [
        "Organizer One",
        "Organizer Two",
    ] or {o.name for o in detail.co_organizers} == {"Organizer One", "Organizer Two"}
    assert detail.event_place.name == "Rathaus"
    assert detail.admin_unit.name == "Meine Crew"
    assert detail.photo.license.name
    assert detail.references == []
    assert detail.reference_requests == []
    assert detail.created_by_label is None
    assert detail.tags == "music,live"
    assert detail.internal_tags == "secret,inhouse"


def test_references_and_the_reference_of_the_calling_organization(read_repo, world):
    detail = read_repo("get_detail", world["other"], world["a"])

    assert detail.reference_id == world["reference"]
    assert [
        (r.admin_unit.name, r.admin_unit.is_verified) for r in detail.references
    ] == [("Meine Crew", True)]
    assert read_repo("get_detail", world["other"], None).reference_id is None


def test_reference_requests(app, db, seeder, read_repo, world):
    seeder.create_reference_request(world["full"], world["b"])

    detail = read_repo("get_detail", world["full"], None)

    assert [r.admin_unit.name for r in detail.reference_requests] == ["Other Crew"]
    assert detail.reference_requests[0].review_status is not None


def test_audit_labels_come_from_the_creator(app, db, seeder, read_repo, world):
    from project.models import Event, User

    with app.app_context():
        user = User.query.first()
        db.session.get(Event, world["full"]).created_by_id = user.id
        db.session.commit()
        email = user.email

    assert read_repo("get_detail", world["full"], None).created_by_label == email


def test_unknown_detail_is_none(read_repo, world):
    assert read_repo("get_detail", 4711, None) is None
    assert read_repo("get_date_detail", 4711) is None


def test_date_detail_carries_the_event(read_repo, world):
    detail = read_repo("get_date_detail", 1)

    assert detail.id == 1
    assert detail.event.id == world["full"]
    assert detail.event.admin_unit.is_verified
    assert detail.end is not None


def test_dates_of_an_event_are_paged_by_start(read_repo, world):
    page = read_repo("list_dates_of_event", world["recurring"], PageRequest(per_page=2))

    assert page.total == 3
    assert len(page.items) == 2
    assert page.items[0].start < page.items[1].start
    assert page.has_next


def test_upcoming_dates_skip_the_past(read_repo, world):
    assert read_repo("list_upcoming_dates", world["past"]) == []

    dates = read_repo("list_upcoming_dates", world["recurring"])
    assert len(dates) == 3
    assert [d.start for d in dates] == sorted(d.start for d in dates)


def test_detail_runs_a_bounded_number_of_statements(app, db, read_repo, world):
    statements = []

    def count(conn, cursor, statement, *args):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    with app.app_context():
        engine = db.engine

    sa_event.listen(engine, "before_cursor_execute", count)
    try:
        read_repo("get_detail", world["full"], world["a"])
    finally:
        sa_event.remove(engine, "before_cursor_execute", count)

    assert len(statements) <= 14


def test_edit_model_carries_the_photo_data_and_form_fields(read_repo, world):
    edit = read_repo("get_for_edit", world["full"])

    assert edit.name == "Full Event"
    assert edit.photo.data
    assert edit.photo.license.code == "CC BY 4.0"
    assert {o.name for o in edit.co_organizers} == {"Organizer One", "Organizer Two"}
    assert edit.custom_categories[0].category_set_id == 1
    assert edit.date_definitions[0].start
    assert read_repo("get_for_edit", world["draft"]).photo is None
    assert read_repo("get_for_edit", 4711) is None
