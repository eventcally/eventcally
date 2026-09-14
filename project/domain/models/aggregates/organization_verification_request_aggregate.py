from __future__ import annotations

from typing import Optional

from project.domain.errors import ConstraintError
from project.domain.events.organization_verification_request_reviewed import (
    OrganizationVerificationRequestReviewed,
)
from project.domain.events.organization_verification_requested import (
    OrganizationVerificationRequested,
)
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from project.domain.types.object_id import ObjectId


class OrganizationVerificationRequestAggregate(BaseAggregate):
    id: ObjectId
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
    review_status: OrganizationVerificationRequestReviewStatus = (
        OrganizationVerificationRequestReviewStatus.inbox
    )
    rejection_reason: Optional[OrganizationVerificationRequestRejectionReason] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        source_admin_unit_id: ObjectId,
        target_admin_unit_id: ObjectId,
    ) -> OrganizationVerificationRequestAggregate:
        if source_admin_unit_id == target_admin_unit_id:
            raise ConstraintError("There must be no self-reference.")

        instance = cls(
            id=-1,
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
            review_status=OrganizationVerificationRequestReviewStatus.inbox,
        )

        event = OrganizationVerificationRequested(
            actor=actor,
            id=-1,
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
        )
        instance.domain_events.append(event)

        return instance

    def _ensure_not_yet_reviewed(self):
        if self.review_status != OrganizationVerificationRequestReviewStatus.inbox:
            raise ConstraintError("Verification request already reviewed.")

    def approve(self, actor: Actor):
        self._ensure_not_yet_reviewed()

        self.review_status = OrganizationVerificationRequestReviewStatus.verified
        self.rejection_reason = None

        self.domain_events.append(
            OrganizationVerificationRequestReviewed(
                actor=actor,
                id=self.id,
                source_admin_unit_id=self.source_admin_unit_id,
                target_admin_unit_id=self.target_admin_unit_id,
                review_status=self.review_status,
            )
        )

    def reject(
        self,
        actor: Actor,
        rejection_reason: Optional[
            OrganizationVerificationRequestRejectionReason
        ] = None,
    ):
        self._ensure_not_yet_reviewed()

        self.review_status = OrganizationVerificationRequestReviewStatus.rejected
        self.rejection_reason = rejection_reason

        self.domain_events.append(
            OrganizationVerificationRequestReviewed(
                actor=actor,
                id=self.id,
                source_admin_unit_id=self.source_admin_unit_id,
                target_admin_unit_id=self.target_admin_unit_id,
                review_status=self.review_status,
            )
        )

    def delete(self, actor: Actor):
        pass
