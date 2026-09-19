from __future__ import annotations

from typing import Optional

from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property

from project.domain.models.aggregates.organization_verification_request_aggregate import (
    OrganizationVerificationRequestAggregate,
)
from project.extensions import db
from project.models.admin_unit_verification_request_generated import (
    AdminUnitVerificationRequestGeneratedMixin,
    AdminUnitVerificationRequestReviewStatus,
)
from project.utils import make_check_violation


class AdminUnitVerificationRequest(
    db.Model, AdminUnitVerificationRequestGeneratedMixin
):
    @hybrid_property
    def verified(self):
        return self.review_status == AdminUnitVerificationRequestReviewStatus.verified

    @classmethod
    def from_aggregate(
        cls, aggregate: OrganizationVerificationRequestAggregate
    ) -> AdminUnitVerificationRequest:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: OrganizationVerificationRequestAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.source_admin_unit_id = aggregate.source_admin_unit_id
        self.target_admin_unit_id = aggregate.target_admin_unit_id
        self.review_status = aggregate.review_status
        self.rejection_reason = aggregate.rejection_reason

    @classmethod
    def to_aggregate(
        cls, model: Optional[AdminUnitVerificationRequest]
    ) -> Optional[OrganizationVerificationRequestAggregate]:
        if model is None:  # pragma: no cover
            return None

        return OrganizationVerificationRequestAggregate(
            id=model.id,
            source_admin_unit_id=model.source_admin_unit_id,
            target_admin_unit_id=model.target_admin_unit_id,
            review_status=(model.review_status.value if model.review_status else None),
            rejection_reason=(
                model.rejection_reason.value if model.rejection_reason else None
            ),
        )

    def validate(self):
        source_id = (
            self.source_admin_unit.id
            if self.source_admin_unit
            else self.source_admin_unit_id
        )
        target_id = (
            self.target_admin_unit.id
            if self.target_admin_unit
            else self.target_admin_unit_id
        )
        if source_id == target_id:  # pragma: no cover
            raise make_check_violation("There must be no self-reference.")


@listens_for(AdminUnitVerificationRequest, "before_insert")
@listens_for(AdminUnitVerificationRequest, "before_update")
def before_saving_admin_unit_verification_request(mapper, connect, self):
    if self.review_status != AdminUnitVerificationRequestReviewStatus.rejected:
        self.rejection_reason = None

    self.validate()
