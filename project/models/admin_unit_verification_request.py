from enum import IntEnum

from sqlalchemy import CheckConstraint, Column, Integer, UniqueConstraint
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property

from project import db
from project.dbtypes import IntegerEnum
from project.models.trackable_mixin import TrackableMixin
from project.utils import make_check_violation


class AdminUnitVerificationRequestReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class AdminUnitVerificationRequestRejectionReason(IntEnum):
    notresponsible = 1
    missinginformation = 2
    unknown = 3
    untrustworthy = 4
    illegal = 5
    irrelevant = 6


class AdminUnitVerificationRequest(db.Model, TrackableMixin):
    __tablename__ = "adminunitverificationrequest"
    __table_args__ = (
        UniqueConstraint("source_admin_unit_id", "target_admin_unit_id"),
        CheckConstraint(
            "source_admin_unit_id != target_admin_unit_id",
            name="auvr_source_neq_target",
        ),
    )
    __model_name__ = "organization_verification_request"
    __display_name__ = "Organization verification request"
    id = Column(Integer(), primary_key=True)
    source_admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
    )
    target_admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
    )
    review_status = Column(IntegerEnum(AdminUnitVerificationRequestReviewStatus))
    rejection_reason = Column(IntegerEnum(AdminUnitVerificationRequestRejectionReason))

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
