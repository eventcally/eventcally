from project.domain.events.event_reference_request_auto_verified import (
    EventReferenceRequestAutoVerified,
)
from project.domain.events.event_reference_request_created import (
    EventReferenceRequestCreated,
)
from project.domain.models.aggregates.event_reference_request_aggregate import (
    EventReferenceRequestAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.infrastructure.models.event_reference_request import EventReferenceRequest
from project.infrastructure.repositories.sql_alchemy_event_reference_request_repository import (
    SqlAlchemyEventReferenceRequestRepository,
)


def _setup(seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    event_id = seeder.create_event(admin_unit_id)
    return Actor(user_id=user_id), other_admin_unit_id, event_id


def test_add_sets_ids_on_created_event_and_roundtrips(app, db, seeder):
    actor, other_admin_unit_id, event_id = _setup(seeder)
    with app.app_context():
        repo = SqlAlchemyEventReferenceRequestRepository(db.session)
        request = EventReferenceRequestAggregate.create(
            actor=actor, admin_unit_id=other_admin_unit_id, event_id=event_id
        )

        repo.add(request)
        db.session.commit()

        loaded = repo.get(request.id)
        created = request.get_first_domain_event_by_type(EventReferenceRequestCreated)
        assert created.id == request.id
        assert loaded.admin_unit_id == other_admin_unit_id
        assert loaded.event_id == event_id
        assert loaded.review_status == EventReferenceRequestReviewStatus.inbox
        assert loaded.rejection_reason is None


def test_add_auto_verified_sets_id_on_auto_verified_event(app, db, seeder):
    actor, other_admin_unit_id, event_id = _setup(seeder)
    with app.app_context():
        repo = SqlAlchemyEventReferenceRequestRepository(db.session)
        request = EventReferenceRequestAggregate.create(
            actor=actor,
            admin_unit_id=other_admin_unit_id,
            event_id=event_id,
            auto_verified=True,
        )

        repo.add(request)
        db.session.commit()

        auto_verified = request.get_first_domain_event_by_type(
            EventReferenceRequestAutoVerified
        )
        assert auto_verified.id == request.id
        assert (
            repo.get(request.id).review_status
            == EventReferenceRequestReviewStatus.verified
        )


def test_update_reject_with_reason_then_remove(app, db, seeder):
    actor, other_admin_unit_id, event_id = _setup(seeder)
    with app.app_context():
        repo = SqlAlchemyEventReferenceRequestRepository(db.session)
        request = EventReferenceRequestAggregate.create(
            actor=actor, admin_unit_id=other_admin_unit_id, event_id=event_id
        )
        repo.add(request)
        db.session.commit()

        request.reject(
            actor=actor,
            rejection_reason=EventReferenceRequestRejectionReason.irrelevant,
        )
        repo.update(request)
        db.session.commit()

        model = db.session.get(EventReferenceRequest, request.id)
        assert model.review_status == EventReferenceRequestReviewStatus.rejected
        assert model.rejection_reason == EventReferenceRequestRejectionReason.irrelevant

        repo.remove(request)
        db.session.commit()
        assert repo.get(request.id) is None
