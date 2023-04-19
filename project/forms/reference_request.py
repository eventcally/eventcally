from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.fields import BooleanField
from wtforms.validators import DataRequired, Optional

from project.forms.common import event_rating_choices
from project.models import (
    EventReferenceRequestRejectionReason,
    EventReferenceRequestReviewStatus,
)


class CreateEventReferenceRequestForm(FlaskForm):
    admin_unit_id = SelectField(
        lazy_gettext("Organization"), validators=[DataRequired()], coerce=int
    )
    submit = SubmitField(lazy_gettext("Save request"))


class DeleteReferenceRequestForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete request"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])


class ReferenceRequestReviewForm(FlaskForm):
    review_status = SelectField(
        lazy_gettext("Review status"),
        coerce=int,
        choices=[
            (
                int(EventReferenceRequestReviewStatus.inbox),
                lazy_gettext("EventReferenceRequestReviewStatus.inbox"),
            ),
            (
                int(EventReferenceRequestReviewStatus.verified),
                lazy_gettext("EventReferenceRequestReviewStatus.verified"),
            ),
            (
                int(EventReferenceRequestReviewStatus.rejected),
                lazy_gettext("EventReferenceRequestReviewStatus.rejected"),
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
                lazy_gettext("EventReferenceRequestRejectionReason.noreason"),
            ),
            (
                int(EventReferenceRequestRejectionReason.duplicate),
                lazy_gettext("EventReferenceRequestRejectionReason.duplicate"),
            ),
            (
                int(EventReferenceRequestRejectionReason.untrustworthy),
                lazy_gettext("EventReferenceRequestRejectionReason.untrustworthy"),
            ),
            (
                int(EventReferenceRequestRejectionReason.irrelevant),
                lazy_gettext("EventReferenceRequestRejectionReason.irrelevant"),
            ),
            (
                int(EventReferenceRequestRejectionReason.illegal),
                lazy_gettext("EventReferenceRequestRejectionReason.illegal"),
            ),
        ],
        description=lazy_gettext("Choose why you rejected the request."),
    )

    rating = SelectField(
        lazy_gettext("Rating"),
        default=50,
        coerce=int,
        choices=event_rating_choices,
        description=lazy_gettext(
            "Choose how relevant the event is to your organization. The value is not visible and is used for sorting."
        ),
    )

    auto_verify = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        validators=[Optional()],
    )

    submit = SubmitField(lazy_gettext("Save review"))
