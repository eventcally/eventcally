import pytest

from project.domain.errors import ConstraintError
from project.domain.events.event_reference_request_auto_verified import (
    EventReferenceRequestAutoVerified,
)
from project.domain.events.event_reference_request_created import (
    EventReferenceRequestCreated,
)
from project.domain.events.event_reference_request_reviewed import (
    EventReferenceRequestReviewed,
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


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def request_(actor):
    return EventReferenceRequestAggregate.create(
        actor=actor, admin_unit_id=1, event_id=2
    )


class TestEventReferenceRequestAggregateCreate:
    def test_creates_instance(self, actor):
        request = EventReferenceRequestAggregate.create(
            actor=actor, admin_unit_id=1, event_id=2
        )
        assert request.id == -1
        assert request.admin_unit_id == 1
        assert request.event_id == 2
        assert request.review_status == EventReferenceRequestReviewStatus.inbox
        assert request.rejection_reason is None

    def test_appends_created_event(self, actor):
        request = EventReferenceRequestAggregate.create(
            actor=actor, admin_unit_id=1, event_id=2
        )
        event = request.get_first_domain_event_by_type(EventReferenceRequestCreated)
        assert event is not None
        assert event.admin_unit_id == 1
        assert event.event_id == 2

    def test_auto_verified_sets_verified_status(self, actor):
        request = EventReferenceRequestAggregate.create(
            actor=actor, admin_unit_id=1, event_id=2, auto_verified=True
        )
        assert request.review_status == EventReferenceRequestReviewStatus.verified

    def test_auto_verified_appends_auto_verified_event_not_created(self, actor):
        request = EventReferenceRequestAggregate.create(
            actor=actor, admin_unit_id=1, event_id=2, auto_verified=True
        )
        event = request.get_first_domain_event_by_type(
            EventReferenceRequestAutoVerified
        )
        assert event is not None
        assert event.admin_unit_id == 1
        assert event.event_id == 2
        assert (
            request.get_first_domain_event_by_type(EventReferenceRequestCreated) is None
        )


class TestEventReferenceRequestAggregateVerify:
    def test_sets_verified_status(self, request_, actor):
        request_.verify(actor)
        assert request_.review_status == EventReferenceRequestReviewStatus.verified
        assert request_.rejection_reason is None

    def test_appends_reviewed_event(self, request_, actor):
        request_.verify(actor)
        event = request_.get_first_domain_event_by_type(EventReferenceRequestReviewed)
        assert event is not None
        assert event.review_status == EventReferenceRequestReviewStatus.verified
        assert event.admin_unit_id == request_.admin_unit_id
        assert event.event_id == request_.event_id

    def test_already_verified_raises_constraint_error(self, request_, actor):
        request_.verify(actor)
        with pytest.raises(ConstraintError):
            request_.verify(actor)

    def test_reject_after_verify_raises_constraint_error(self, request_, actor):
        request_.verify(actor)
        with pytest.raises(ConstraintError):
            request_.reject(actor)


class TestEventReferenceRequestAggregateReject:
    def test_sets_rejected_status_and_reason(self, request_, actor):
        request_.reject(actor, EventReferenceRequestRejectionReason.untrustworthy)
        assert request_.review_status == EventReferenceRequestReviewStatus.rejected
        assert (
            request_.rejection_reason
            == EventReferenceRequestRejectionReason.untrustworthy
        )

    def test_reject_without_reason(self, request_, actor):
        request_.reject(actor)
        assert request_.review_status == EventReferenceRequestReviewStatus.rejected
        assert request_.rejection_reason is None

    def test_appends_reviewed_event(self, request_, actor):
        request_.reject(actor)
        event = request_.get_first_domain_event_by_type(EventReferenceRequestReviewed)
        assert event is not None
        assert event.review_status == EventReferenceRequestReviewStatus.rejected

    def test_reject_after_reject_does_not_raise(self, request_, actor):
        request_.reject(actor)
        request_.reject(actor)
        assert request_.review_status == EventReferenceRequestReviewStatus.rejected

    def test_verify_after_reject_succeeds(self, request_, actor):
        request_.reject(actor)
        request_.verify(actor)
        assert request_.review_status == EventReferenceRequestReviewStatus.verified


class TestEventReferenceRequestAggregateDelete:
    def test_delete_does_not_raise(self, request_, actor):
        request_.delete(actor)
