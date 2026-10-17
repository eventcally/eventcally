"""SqlAlchemyEventReferenceReadRepository against the database."""

import pytest
from sqlalchemy import text

from project.application.queries import (
    ListIncomingEventReferencesQuery,
    ListOutgoingEventReferencesQuery,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.event_reference_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def test_incoming_outgoing_and_get(app, db, read_repo, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Andere Crew")
    first_id = seeder.create_reference(
        seeder.create_event(other_admin_unit_id, name="Erstes"), admin_unit_id
    )
    second_id = seeder.create_reference(
        seeder.create_event(other_admin_unit_id, name="Zweites"), admin_unit_id
    )

    with app.app_context():
        db.session.execute(
            text("UPDATE eventreference SET created_at = '2026-01-01' WHERE id = :id"),
            {"id": first_id},
        )
        db.session.commit()

    incoming = read_repo(
        "list_incoming", ListIncomingEventReferencesQuery(admin_unit_id=admin_unit_id)
    )
    outgoing = read_repo(
        "list_outgoing",
        ListOutgoingEventReferencesQuery(admin_unit_id=other_admin_unit_id),
    )
    reference = read_repo("get", first_id)

    assert [item.id for item in incoming.items] == [second_id, first_id]
    assert [item.id for item in outgoing.items] == [second_id, first_id]
    assert reference.event.name == "Erstes"
    assert reference.event.admin_unit.name == "Andere Crew"
    assert reference.admin_unit.name == "Meine Crew"
    assert reference.admin_unit_id == admin_unit_id
    assert read_repo("get", 4711) is None
    assert (
        read_repo(
            "list_outgoing",
            ListOutgoingEventReferencesQuery(admin_unit_id=admin_unit_id),
        ).total
        == 0
    )


def test_trackable_filters_and_sort(app, db, read_repo, seeder):
    from datetime import datetime

    from project.application.queries import TrackableCriteria, TrackableSort
    from tests.api.read_parity import set_trackable

    _, admin_unit_id = seeder.setup_base(log_in=False)
    other_admin_unit_id = seeder.create_admin_unit(
        seeder.create_user("other@test.de"), "Andere Crew"
    )
    first_id = seeder.create_reference(
        seeder.create_event(other_admin_unit_id), admin_unit_id
    )
    second_id = seeder.create_reference(
        seeder.create_event(other_admin_unit_id), admin_unit_id
    )

    with app.app_context():
        set_trackable(
            db, "eventreference", first_id, datetime(2026, 1, 1), datetime(2026, 3, 1)
        )
        set_trackable(db, "eventreference", second_id, datetime(2026, 2, 1))
        db.session.commit()

    def ids(**kwargs):
        page = read_repo(
            "list_incoming",
            ListIncomingEventReferencesQuery(admin_unit_id=admin_unit_id, **kwargs),
        )
        return [item.id for item in page.items]

    assert ids() == [second_id, first_id]
    assert ids(sort=TrackableSort.last_modified_at_desc) == [first_id, second_id]
    assert ids(sort=TrackableSort.updated_at_desc) == [first_id, second_id]
    assert ids(trackable=TrackableCriteria(created_at_to=datetime(2026, 1, 15))) == [
        first_id
    ]
    assert read_repo("get", first_id).updated_at == datetime(2026, 3, 1)
