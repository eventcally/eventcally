from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
)
from wtforms.fields import EmailField, TelField
from wtforms.validators import DataRequired, Optional

from project.forms.common import get_accept_tos_markup
from project.forms.event import EventDateDefinitionFormMixin, SharedEventForm
from project.forms.widgets import TagSelectField
from project.models import (
    EventAttendanceMode,
    EventRejectionReason,
    EventTargetGroupOrigin,
    Image,
)


class CreateEventSuggestionForm(SharedEventForm, EventDateDefinitionFormMixin):
    contact_name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        description=lazy_gettext("Please enter your name for the review."),
    )
    contact_phone = TelField(
        lazy_gettext("Phone"),
        validators=[Optional()],
        description=lazy_gettext(
            "Please enter your phone number or email address for the review."
        ),
    )
    contact_email = EmailField(
        lazy_gettext("Email"),
        validators=[Optional()],
        description=lazy_gettext(
            "Please enter your email address or phone number for the review."
        ),
    )
    contact_email_notice = BooleanField(
        lazy_gettext("I would like to be notified by email after the review"),
        validators=[Optional()],
    )

    event_place_id = TagSelectField(
        lazy_gettext("Place"),
        validators=[DataRequired()],
        description=lazy_gettext(
            "Choose where the event takes place. If the venue is not yet in the list, just enter it."
        ),
    )
    event_place_id_suffix = StringField(
        validators=[Optional()],
    )
    organizer_id = TagSelectField(
        lazy_gettext("Organizer"),
        validators=[DataRequired()],
        description=lazy_gettext(
            "Select the organizer. If the organizer is not yet on the list, just enter it."
        ),
    )
    organizer_id_suffix = StringField(
        validators=[Optional()],
    )

    category_ids = SelectMultipleField(
        lazy_gettext("Categories"),
        validators=[Optional()],
        coerce=int,
        description=lazy_gettext("Choose categories that fit the event."),
    )
    accept_tos = BooleanField(validators=[DataRequired()])

    submit = SubmitField(lazy_gettext("Create event suggestion"))

    def __init__(self, **kwargs):
        super(CreateEventSuggestionForm, self).__init__(**kwargs)
        self._fields["accept_tos"].label.text = get_accept_tos_markup()

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "photo" and not obj.photo:
                obj.photo = Image()
            if name == "event_place_id" and self.event_place_id.is_free_text():
                obj.event_place_text = self.event_place_id.data
                obj.event_place_id = None

                if self.event_place_id_suffix.data:
                    obj.event_place_text = (
                        obj.event_place_text + ", " + self.event_place_id_suffix.data
                    )
            elif name == "organizer_id" and self.organizer_id.is_free_text():
                obj.organizer_text = self.organizer_id.data
                obj.organizer_id = None

                if self.organizer_id_suffix.data:
                    obj.organizer_text = (
                        obj.organizer_text + ", " + self.organizer_id_suffix.data
                    )
            elif name == "target_group_origin":
                obj.target_group_origin = EventTargetGroupOrigin(
                    self.target_group_origin.data
                )
            elif name == "attendance_mode":
                obj.attendance_mode = EventAttendanceMode(self.attendance_mode.data)
            else:
                field.populate_obj(obj, name)

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)

        if not self.validate_date_definition():
            result = False

        return result


class RejectEventSuggestionForm(FlaskForm):
    rejection_resaon = SelectField(
        lazy_gettext("Rejection reason"),
        coerce=int,
        choices=[
            (
                0,
                lazy_gettext("EventRejectionReason.noreason"),
            ),
            (
                int(EventRejectionReason.duplicate),
                lazy_gettext("EventRejectionReason.duplicate"),
            ),
            (
                int(EventRejectionReason.untrustworthy),
                lazy_gettext("EventRejectionReason.untrustworthy"),
            ),
            (
                int(EventRejectionReason.illegal),
                lazy_gettext("EventRejectionReason.illegal"),
            ),
        ],
    )

    submit = SubmitField(lazy_gettext("Reject event suggestion"))
