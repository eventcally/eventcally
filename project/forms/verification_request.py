from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.fields import BooleanField
from wtforms.validators import DataRequired, Optional

from project.models import (
    AdminUnitVerificationRequestRejectionReason,
    AdminUnitVerificationRequestReviewStatus,
)


class CreateAdminUnitVerificationRequestForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Request verification"))


class DeleteVerificationRequestForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete request"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])


class VerificationRequestReviewForm(FlaskForm):
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
