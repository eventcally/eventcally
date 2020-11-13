from flask import request
from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    FieldList,
    RadioField,
    DateTimeField,
    StringField,
    SubmitField,
    TextAreaField,
    SelectField,
    BooleanField,
    IntegerField,
    FormField,
)
from wtforms.fields.html5 import DateTimeLocalField, EmailField, TelField, URLField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import html_params, HTMLString
from project.models import (
    EventSuggestion,
    EventPlace,
    EventTargetGroupOrigin,
    EventAttendanceMode,
    EventStatus,
    Location,
    EventOrganizer,
    EventRejectionReason,
    EventReviewStatus,
    Image,
)
from project.forms.common import event_rating_choices, Base64ImageForm
from project.forms.widgets import CustomDateTimeField, CustomDateField, TagSelectField
from project.forms.common import event_rating_choices


class CreateEventSuggestionForm(FlaskForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        description=lazy_gettext("Enter a short, meaningful name for the event."),
    )
    start = CustomDateTimeField(
        lazy_gettext("Start"),
        validators=[DataRequired()],
        description=lazy_gettext("Indicate when the event will take place."),
    )
    description = TextAreaField(
        lazy_gettext("Description"),
        validators=[Optional()],
        description=lazy_gettext("Add an optional description of the event."),
    )
    external_link = URLField(
        lazy_gettext("Link URL"),
        validators=[Optional()],
        description=lazy_gettext(
            "Add an optional link. That can make the review easier."
        ),
    )

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
    organizer_id = TagSelectField(
        lazy_gettext("Organizer"),
        validators=[DataRequired()],
        description=lazy_gettext(
            "Select the organizer. If the organizer is not yet on the list, just enter it."
        ),
    )
    photo = FormField(
        Base64ImageForm,
        lazy_gettext("Photo"),
        default=lambda: Image(),
        description=lazy_gettext(
            "We recommend uploading a photo for the event. It looks a lot more, but of course it works without it."
        ),
    )
    accept_tos = BooleanField(
        lazy_gettext(
            "I confirm that I have clarified all information (text, images, etc.) that I upload into the system with regard to their rights of use and declare that they may be passed on."
        ),
        validators=[DataRequired()],
    )

    submit = SubmitField(lazy_gettext("Create event suggestion"))

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "photo" and not obj.photo:
                obj.photo = Image()
            if name == "event_place_id" and self.event_place_id.is_free_text():
                obj.event_place_text = self.event_place_id.data
                obj.event_place_id = None
            elif name == "organizer_id" and self.organizer_id.is_free_text():
                obj.organizer_text = self.organizer_id.data
                obj.organizer_id = None
            else:
                field.populate_obj(obj, name)


class RejectEventSuggestionForm(FlaskForm):
    rejection_resaon = SelectField(
        lazy_gettext("Rejection reason"),
        coerce=int,
        choices=[
            (0, ""),
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
