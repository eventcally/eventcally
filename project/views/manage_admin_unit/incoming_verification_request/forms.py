from flask_babel import lazy_gettext
from wtforms import BooleanField, SelectField, SubmitField
from wtforms.validators import Optional

from project.application.commands import (
    ApproveOrganizationVerificationRequestCommand,
    RejectOrganizationVerificationRequestCommand,
)
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.models import (
    AdminUnitVerificationRequestRejectionReason,
    AdminUnitVerificationRequestReviewStatus,
)
from project.modular.base_form import BaseForm


class VerificationRequestReviewForm(BaseForm):
    review_status = SelectField(
        lazy_gettext("Review status"),
        coerce=int,
        choices=[
            (
                int(AdminUnitVerificationRequestReviewStatus.inbox),
                lazy_gettext("AdminUnitVerificationRequestReviewStatus.inbox"),
            ),
            (
                int(AdminUnitVerificationRequestReviewStatus.verified),
                lazy_gettext("AdminUnitVerificationRequestReviewStatus.verified"),
            ),
            (
                int(AdminUnitVerificationRequestReviewStatus.rejected),
                lazy_gettext("AdminUnitVerificationRequestReviewStatus.rejected"),
            ),
        ],
        description=lazy_gettext("Choose the result of your review."),
    )

    rejection_reason = SelectField(
        lazy_gettext("Rejection reason"),
        coerce=int,
        choices=[
            (
                0,
                lazy_gettext("AdminUnitVerificationRequestRejectionReason.noreason"),
            ),
            (
                int(AdminUnitVerificationRequestRejectionReason.notresponsible),
                lazy_gettext(
                    "AdminUnitVerificationRequestRejectionReason.notresponsible"
                ),
            ),
            (
                int(AdminUnitVerificationRequestRejectionReason.missinginformation),
                lazy_gettext(
                    "AdminUnitVerificationRequestRejectionReason.missinginformation"
                ),
            ),
            (
                int(AdminUnitVerificationRequestRejectionReason.unknown),
                lazy_gettext("AdminUnitVerificationRequestRejectionReason.unknown"),
            ),
            (
                int(AdminUnitVerificationRequestRejectionReason.untrustworthy),
                lazy_gettext(
                    "AdminUnitVerificationRequestRejectionReason.untrustworthy"
                ),
            ),
            (
                int(AdminUnitVerificationRequestRejectionReason.illegal),
                lazy_gettext("AdminUnitVerificationRequestRejectionReason.illegal"),
            ),
            (
                int(AdminUnitVerificationRequestRejectionReason.irrelevant),
                lazy_gettext("AdminUnitVerificationRequestRejectionReason.irrelevant"),
            ),
        ],
        description=lazy_gettext("Choose why you rejected the request."),
    )

    auto_verify = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        validators=[Optional()],
    )

    submit = SubmitField(lazy_gettext("Save review"))

    def create_approve_command(
        self, verification_request_id: int
    ) -> ApproveOrganizationVerificationRequestCommand:
        return ApproveOrganizationVerificationRequestCommand(
            actor=self.get_current_actor(),
            id=verification_request_id,
            auto_verify_event_reference_requests=(
                self.auto_verify.data if self.auto_verify.data else None
            ),
        )

    def create_reject_command(
        self, verification_request_id: int
    ) -> RejectOrganizationVerificationRequestCommand:
        return RejectOrganizationVerificationRequestCommand(
            actor=self.get_current_actor(),
            id=verification_request_id,
            rejection_reason=(
                OrganizationVerificationRequestRejectionReason(
                    self.rejection_reason.data
                )
                if self.rejection_reason.data
                else None
            ),
        )
