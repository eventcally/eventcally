from flask_babel import lazy_gettext
from wtforms import BooleanField, SelectField, SubmitField
from wtforms.validators import Optional

from project.forms.common import event_rating_choices
from project.models import (
    EventReferenceRequestRejectionReason,
    EventReferenceRequestReviewStatus,
)
from project.modular.base_form import BaseForm


class BaseEventReferenceRequestForm(BaseForm):
    rating = SelectField(
        lazy_gettext("Rating"),
        default=50,
        coerce=int,
        choices=event_rating_choices,
        description=lazy_gettext(
            "Choose how relevant the event is to your organization. The value is not visible and is used for sorting."
        ),
    )


class UpdateEventReferenceRequestForm(BaseEventReferenceRequestForm):
    submit = SubmitField(lazy_gettext("Update reference request"))


class DeleteEventReferenceRequestForm(BaseForm):
    submit = SubmitField(lazy_gettext("Delete reference request"))


class ReferenceRequestReviewForm(BaseForm):
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
