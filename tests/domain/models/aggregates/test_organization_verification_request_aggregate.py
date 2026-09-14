import pytest

from project.domain.errors import ConstraintError
from project.domain.events.organization_verification_request_reviewed import (
    OrganizationVerificationRequestReviewed,
)
from project.domain.events.organization_verification_requested import (
    OrganizationVerificationRequested,
)
from project.domain.models.aggregates.organization_verification_request_aggregate import (
    OrganizationVerificationRequestAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def request_(actor):
    return OrganizationVerificationRequestAggregate.create(
        actor=actor, source_admin_unit_id=1, target_admin_unit_id=2
    )


class TestOrganizationVerificationRequestAggregateCreate:
    def test_creates_instance(self, actor):
        request = OrganizationVerificationRequestAggregate.create(
            actor=actor, source_admin_unit_id=1, target_admin_unit_id=2
        )
        assert request.id == -1
        assert request.source_admin_unit_id == 1
        assert request.target_admin_unit_id == 2
        assert (
            request.review_status == OrganizationVerificationRequestReviewStatus.inbox
        )
        assert request.rejection_reason is None

    def test_self_reference_raises_constraint_error(self, actor):
        with pytest.raises(ConstraintError):
            OrganizationVerificationRequestAggregate.create(
                actor=actor, source_admin_unit_id=1, target_admin_unit_id=1
            )

    def test_appends_requested_event(self, actor):
        request = OrganizationVerificationRequestAggregate.create(
            actor=actor, source_admin_unit_id=1, target_admin_unit_id=2
        )
        event = request.get_first_domain_event_by_type(
            OrganizationVerificationRequested
        )
        assert event is not None
        assert event.source_admin_unit_id == 1
        assert event.target_admin_unit_id == 2


class TestOrganizationVerificationRequestAggregateApprove:
    def test_sets_verified_status(self, request_, actor):
        request_.approve(actor)
        assert request_.review_status == (
            OrganizationVerificationRequestReviewStatus.verified
        )
        assert request_.rejection_reason is None

    def test_appends_reviewed_event(self, request_, actor):
        request_.approve(actor)
        event = request_.get_first_domain_event_by_type(
            OrganizationVerificationRequestReviewed
        )
        assert event is not None
        assert event.review_status == (
            OrganizationVerificationRequestReviewStatus.verified
        )
        assert event.source_admin_unit_id == request_.source_admin_unit_id
        assert event.target_admin_unit_id == request_.target_admin_unit_id

    def test_already_reviewed_raises_constraint_error(self, request_, actor):
        request_.approve(actor)
        with pytest.raises(ConstraintError):
            request_.approve(actor)


class TestOrganizationVerificationRequestAggregateReject:
    def test_sets_rejected_status_and_reason(self, request_, actor):
        request_.reject(
            actor, OrganizationVerificationRequestRejectionReason.untrustworthy
        )
        assert request_.review_status == (
            OrganizationVerificationRequestReviewStatus.rejected
        )
        assert (
            request_.rejection_reason
            == OrganizationVerificationRequestRejectionReason.untrustworthy
        )

    def test_reject_without_reason(self, request_, actor):
        request_.reject(actor)
        assert request_.review_status == (
            OrganizationVerificationRequestReviewStatus.rejected
        )
        assert request_.rejection_reason is None

    def test_appends_reviewed_event(self, request_, actor):
        request_.reject(actor)
        event = request_.get_first_domain_event_by_type(
            OrganizationVerificationRequestReviewed
        )
        assert event is not None
        assert event.review_status == (
            OrganizationVerificationRequestReviewStatus.rejected
        )

    def test_already_reviewed_raises_constraint_error(self, request_, actor):
        request_.reject(actor)
        with pytest.raises(ConstraintError):
            request_.reject(actor)


class TestOrganizationVerificationRequestAggregateDelete:
    def test_delete_does_not_raise(self, request_, actor):
        request_.delete(actor)
