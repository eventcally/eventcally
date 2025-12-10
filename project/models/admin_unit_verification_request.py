from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property

from project import db
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

    if self.rejection_reason == 0:
        self.rejection_reason = None

    self.validate()
