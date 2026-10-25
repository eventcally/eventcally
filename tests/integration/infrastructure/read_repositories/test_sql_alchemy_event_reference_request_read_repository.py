"""SqlAlchemyEventReferenceRequestReadRepository against the database."""

import pytest
from sqlalchemy import text

from project.application.queries import (
    ListIncomingEventReferenceRequestsQuery,
    ListOutgoingEventReferenceRequestsQuery,
)
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.event_reference_request_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def test_lists_filters_and_get(app, db, read_repo, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Andere Crew")
    old_id = seeder.create_reference_request(
        seeder.create_event(other_admin_unit_id, name="Alt"), admin_unit_id
    )
    new_id = seeder.create_reference_request(
        seeder.create_event(other_admin_unit_id, name="Neu"), admin_unit_id
    )

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE eventreferencerequest SET created_at = '2026-01-01',"
                " review_status = 3, rejection_reason = 1 WHERE id = :id"
            ),
            {"id": old_id},
        )
        db.session.commit()

    incoming = read_repo(
        "list_incoming",
        ListIncomingEventReferenceRequestsQuery(admin_unit_id=admin_unit_id),
    )
    rejected = read_repo(
        "list_incoming",
        ListIncomingEventReferenceRequestsQuery(
            admin_unit_id=admin_unit_id,
            review_status=EventReferenceRequestReviewStatus.rejected,
        ),
    )
    outgoing = read_repo(
        "list_outgoing",
        ListOutgoingEventReferenceRequestsQuery(admin_unit_id=other_admin_unit_id),
    )
    old = read_repo("get", old_id)

    assert [item.id for item in incoming.items] == [new_id, old_id]
    assert [item.id for item in rejected.items] == [old_id]
    assert [item.id for item in outgoing.items] == [new_id, old_id]
    assert old.review_status == EventReferenceRequestReviewStatus.rejected
    assert old.rejection_reason == EventReferenceRequestRejectionReason.duplicate
    assert old.event.admin_unit.id == other_admin_unit_id
    assert old.admin_unit.name == "Meine Crew"
    assert read_repo("get", new_id).rejection_reason is None
    assert read_repo("get", 4711) is None


def test_organization_exists_and_auto_verifies(app, db, read_repo, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_admin_unit_relation(
        admin_unit_id, other_admin_unit_id, auto_verify_event_reference_requests=True
    )

    assert read_repo("organization_exists", admin_unit_id) is True
    assert read_repo("organization_exists", 4711) is False
    assert read_repo("auto_verifies", admin_unit_id, other_admin_unit_id) is True
    assert read_repo("auto_verifies", other_admin_unit_id, admin_unit_id) is False
