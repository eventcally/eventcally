from dateutil.relativedelta import relativedelta
from flask import request
from flask_babel import gettext, lazy_gettext
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FormField,
    HiddenField,
    IntegerField,
    RadioField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields import EmailField, FieldList, URLField
from wtforms.validators import DataRequired, Length, Optional

from project.forms.common import (
    Base64ImageForm,
    LocationForm,
    distance_choices,
    event_rating_choices,
)
from project.forms.widgets import (
    CustomDateField,
    CustomDateTimeField,
    HTML5StringField,
    MultiCheckboxField,
)
from project.models import (
    EventAttendanceMode,
    EventDateDefinition,
    EventOrganizer,
    EventPlace,
    EventStatus,
    EventTargetGroupOrigin,
    Image,
    Location,
    PublicStatus,
)


class EventDateDefinitionFormMixin:
    start = CustomDateTimeField(
        lazy_gettext("Start"),
        validators=[DataRequired()],
        description=lazy_gettext("Indicate when the event date will start."),
    )
    end = CustomDateTimeField(
        lazy_gettext("End"),
        validators=[Optional()],
        description=lazy_gettext(
            "Indicate when the event date will end. An event can last a maximum of 180 days."
        ),
    )
    allday = BooleanField(
        lazy_gettext("All-day"),
        validators=[Optional()],
    )
    recurrence_rule = TextAreaField(
        lazy_gettext("Recurring event"),
        validators=[Optional()],
    )

    def validate_date_definition(self):
        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                msg = gettext("The start must be before the end.")
                self.start.errors.append(msg)
                return False

            max_end = self.start.data + relativedelta(days=180)
            if self.end.data > max_end:
                msg = gettext("An event can last a maximum of 180 days.")
                self.end.errors.append(msg)
                return False
        return True


class EventDateDefinitionForm(FlaskForm, EventDateDefinitionFormMixin):
    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)

        if not self.validate_date_definition():
            result = False

        return result


class EventPlaceForm(FlaskForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[Optional()],
    )
    location = FormField(LocationForm, default=lambda: Location())

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "location" and not obj.location:
                obj.location = Location()
            field.populate_obj(obj, name)


class OrganizerForm(EventPlaceForm):
    pass


class EventOrganizerForm(FlaskForm):
    name = StringField(
        lazy_gettext("Organizator"),
        validators=[Optional(), Length(max=255)],
    )
    url = URLField(lazy_gettext("Link URL"), validators=[Optional(), Length(max=255)])
    email = EmailField(lazy_gettext("Email"), validators=[Optional(), Length(max=255)])
    phone = StringField(lazy_gettext("Phone"), validators=[Optional(), Length(max=255)])
    fax = StringField(lazy_gettext("Fax"), validators=[Optional(), Length(max=255)])


class SharedEventForm(FlaskForm):
    name = HTML5StringField(
        lazy_gettext("Name"),
        validators=[DataRequired(), Length(min=3, max=255)],
        description=lazy_gettext("Enter a short, meaningful name for the event."),
    )
    description = TextAreaField(
        lazy_gettext("Description"),
        validators=[Optional()],
        description=lazy_gettext("Add an description of the event."),
    )
    external_link = URLField(
        lazy_gettext("Link URL"),
        validators=[Optional(), Length(max=255)],
        description=lazy_gettext(
            "Enter a link to an external website containing more information about the event."
        ),
    )
    ticket_link = URLField(
        lazy_gettext("Ticket Link URL"),
        validators=[Optional(), Length(max=255)],
        description=lazy_gettext("Enter a link where tickets can be purchased."),
    )
    tags = StringField(
        lazy_gettext("Tags"),
        validators=[Optional()],
        description=lazy_gettext(
            "Enter keywords with which the event should be found. Words do not need to be entered if they are already in the name or description."
        ),
    )
    kid_friendly = BooleanField(
        lazy_gettext("Kid friendly"),
        validators=[Optional()],
        description=lazy_gettext("If the event is particularly suitable for children."),
    )
    accessible_for_free = BooleanField(
        lazy_gettext("Accessible for free"),
        validators=[Optional()],
        description=lazy_gettext("If the event is accessible for free."),
    )
    age_from = IntegerField(
        lazy_gettext("Typical Age from"),
        validators=[Optional()],
        description=lazy_gettext("The minimum age that participants should be."),
    )
    age_to = IntegerField(
        lazy_gettext("Typical Age to"),
        validators=[Optional()],
        description=lazy_gettext("The maximum age that participants should be."),
    )
    registration_required = BooleanField(
        lazy_gettext("Registration required"),
        validators=[Optional()],
        description=lazy_gettext(
            "If the participants needs to register for the event."
        ),
    )
    booked_up = BooleanField(
        lazy_gettext("Booked up"),
        validators=[Optional()],
        description=lazy_gettext("If the event is booked up or sold out."),
    )
    expected_participants = IntegerField(
        lazy_gettext("Expected number of participants"),
        validators=[Optional()],
        description=lazy_gettext("The estimated expected attendance."),
    )
    price_info = TextAreaField(
        lazy_gettext("Price info"),
        validators=[Optional()],
        description=lazy_gettext(
            "Enter price information in textual form. E.g., different prices for adults and children."
        ),
    )
    target_group_origin = SelectField(
        lazy_gettext("Target group origin"),
        coerce=int,
        choices=[
            (
                int(EventTargetGroupOrigin.both),
                lazy_gettext("EventTargetGroupOrigin.both"),
            ),
            (
                int(EventTargetGroupOrigin.tourist),
                lazy_gettext("EventTargetGroupOrigin.tourist"),
            ),
            (
                int(EventTargetGroupOrigin.resident),
                lazy_gettext("EventTargetGroupOrigin.resident"),
            ),
        ],
        description=lazy_gettext(
            "Choose whether the event is particularly suitable for tourists or residents."
        ),
    )
    attendance_mode = SelectField(
        lazy_gettext("Attendance mode"),
        coerce=int,
        choices=[
            (
                int(EventAttendanceMode.offline),
                lazy_gettext("EventAttendanceMode.offline"),
            ),
            (
                int(EventAttendanceMode.online),
                lazy_gettext("EventAttendanceMode.online"),
            ),
            (int(EventAttendanceMode.mixed), lazy_gettext("EventAttendanceMode.mixed")),
        ],
        description=lazy_gettext("Choose how people can attend the event."),
    )
    photo = FormField(
        Base64ImageForm,
        lazy_gettext("Photo"),
        default=lambda: Image(),
        description=lazy_gettext(
            "We recommend uploading a photo for the event. It looks a lot more, but of course it works without it."
        ),
    )


class BaseEventForm(SharedEventForm):
    date_definitions = FieldList(
        FormField(EventDateDefinitionForm, default=lambda: EventDateDefinition()),
        min_entries=1,
    )
    date_definition_template = FormField(
        EventDateDefinitionForm, default=lambda: EventDateDefinition()
    )
    previous_start_date = CustomDateTimeField(
        lazy_gettext("Previous start date"),
        validators=[Optional()],
        description=lazy_gettext(
            "Enter when the event should have taken place before it was postponed."
        ),
    )
    category_ids = SelectMultipleField(
        lazy_gettext("Categories"),
        validators=[DataRequired()],
        coerce=int,
        description=lazy_gettext("Choose categories that fit the event."),
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
    co_organizer_ids = SelectMultipleField(
        lazy_gettext("Co-organizers"),
        validators=[Optional()],
        coerce=int,
        description=lazy_gettext(
            "Select optional co-organizers. You can add and modify organizers at Organization > Organizers."
        ),
    )

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)

        if self.co_organizer_ids.data and self.organizer_id.data:
            if self.organizer_id.data in self.co_organizer_ids.data:
                msg = gettext("Invalid co-organizer.")
                self.co_organizer_ids.errors.append(msg)
                result = False

        return result


class CreateEventForm(BaseEventForm):
    event_place_choice = RadioField(
        lazy_gettext("Place"),
        choices=[
            (1, lazy_gettext("Select existing place")),
            (2, lazy_gettext("Enter new place")),
        ],
        default=1,
        coerce=int,
    )
    event_place_id = SelectField(
        lazy_gettext("Place"),
        validators=[Optional()],
        coerce=int,
    )
    new_event_place = FormField(EventPlaceForm, default=lambda: EventPlace())

    organizer_choice = RadioField(
        lazy_gettext("Organizer"),
        choices=[
            (1, lazy_gettext("Select existing organizer")),
            (2, lazy_gettext("Enter new organizer")),
        ],
        default=1,
        coerce=int,
    )
    organizer_id = SelectField(
        lazy_gettext("Organizer"),
        validators=[Optional()],
        coerce=int,
    )
    new_organizer = FormField(OrganizerForm, default=lambda: EventOrganizer())

    reference_request_admin_unit_id = MultiCheckboxField(
        lazy_gettext("Reference requests"), validators=[Optional()], coerce=int
    )

    submit_draft = SubmitField(lazy_gettext("Save as draft"))
    submit_planned = SubmitField(lazy_gettext("Save as planned"))
    submit = SubmitField(lazy_gettext("Publish event"))

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "new_event_place":
                if self.event_place_choice.data != 2:
                    continue
                if not obj.event_place:
                    obj.event_place = EventPlace()
                field.populate_obj(obj, "event_place")
            elif name == "new_organizer":
                if self.organizer_choice.data != 2:
                    continue
                if not obj.organizer:
                    obj.organizer = EventOrganizer()
                field.populate_obj(obj, "organizer")
            elif name == "photo" and not obj.photo:
                obj.photo = Image()
            elif name == "date_definition_template":
                continue
            field.populate_obj(obj, name)

        obj.public_status = (
            PublicStatus.published
            if self.submit.data
            else (
                PublicStatus.planned if self.submit_planned.data else PublicStatus.draft
            )
        )

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)

        if (
            not self.event_place_id.data or self.event_place_id.data == 0
        ) and not self.new_event_place.form.name.data:
            msg = gettext("Select existing place or enter new place")
            self.event_place_id.errors.append(msg)
            self.new_event_place.form.name.errors.append(msg)
            result = False

        if (
            not self.organizer_id.data or self.organizer_id.data == 0
        ) and not self.new_organizer.form.name.data:
            msg = gettext("Select existing organizer or enter new organizer")
            self.organizer_id.errors.append(msg)
            self.new_organizer.form.name.errors.append(msg)
            result = False

        return result


class UpdateEventForm(BaseEventForm):
    event_place_id = SelectField(
        lazy_gettext("Place"),
        validators=[DataRequired()],
        coerce=int,
        description=lazy_gettext(
            "Choose where the event takes place. You can add and modify places at Organization > Places."
        ),
    )
    organizer_id = SelectField(
        lazy_gettext("Organizer"),
        validators=[DataRequired()],
        coerce=int,
        description=lazy_gettext(
            "Select the organizer. You can add and modify organizers at Organization > Organizers."
        ),
    )

    status = SelectField(
        lazy_gettext("Status"),
        coerce=int,
        choices=[
            (int(EventStatus.scheduled), lazy_gettext("EventStatus.scheduled")),
            (int(EventStatus.cancelled), lazy_gettext("EventStatus.cancelled")),
            (int(EventStatus.movedOnline), lazy_gettext("EventStatus.movedOnline")),
            (int(EventStatus.postponed), lazy_gettext("EventStatus.postponed")),
            (int(EventStatus.rescheduled), lazy_gettext("EventStatus.rescheduled")),
        ],
        description=lazy_gettext("Select the status of the event."),
    )

    public_status = SelectField(
        lazy_gettext("Public status"),
        coerce=int,
        choices=[
            (int(PublicStatus.published), lazy_gettext("PublicStatus.published")),
            (int(PublicStatus.planned), lazy_gettext("PublicStatus.planned")),
            (int(PublicStatus.draft), lazy_gettext("PublicStatus.draft")),
        ],
        description=lazy_gettext(
            "Planned events appear in the scheduling view, but not on public calendars."
        ),
    )

    submit = SubmitField(lazy_gettext("Update event"))

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "photo" and not obj.photo:
                obj.photo = Image()
            elif name == "date_definition_template":
                continue
            field.populate_obj(obj, name)

        if obj.photo and obj.photo.is_empty():
            obj.photo = None
            obj.photo_id = None


class DeleteEventForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete event"))


class FindEventForm(FlaskForm):
    class Meta:
        csrf = False

    date_from = CustomDateField(lazy_gettext("From"), validators=[Optional()])
    date_to = CustomDateField(
        lazy_gettext("to"), set_end_of_day=True, validators=[Optional()]
    )
    keyword = StringField(lazy_gettext("Keyword"), validators=[Optional()])
    category_id = SelectField(
        lazy_gettext("Category"), validators=[Optional()], coerce=int
    )
    tag = StringField(lazy_gettext("Tags"), validators=[Optional()])
    organizer_id = SelectField(
        lazy_gettext("Organizer"), validators=[Optional()], coerce=int
    )
    event_place_id = SelectField(
        lazy_gettext("Place"), validators=[Optional()], coerce=int
    )
    coordinate = HiddenField(validators=[Optional()])
    location_name = HiddenField(validators=[Optional()])
    location = SelectField(lazy_gettext("Location"), validators=[Optional()])
    distance = SelectField(
        lazy_gettext("Distance"),
        validators=[Optional()],
        coerce=int,
        choices=distance_choices,
    )
    postal_code = StringField(lazy_gettext("Postal code"), validators=[Optional()])
    exclude_recurring = BooleanField(
        lazy_gettext("Exclude recurring events"),
        validators=[Optional()],
    )
    created_at_from = CustomDateField(lazy_gettext("From"), validators=[Optional()])
    created_at_to = CustomDateField(
        lazy_gettext("to"), set_end_of_day=True, validators=[Optional()]
    )
    sort = SelectField(
        lazy_gettext("Sort"),
        choices=[
            (
                "start",
                lazy_gettext("Earliest start first"),
            ),
            (
                "-created_at",
                lazy_gettext("Newest first"),
            ),
            (
                "-last_modified_at",
                lazy_gettext("Last modified first"),
            ),
        ],
        default="start",
    )

    submit = SubmitField(lazy_gettext("Find events"))

    def is_submitted(self):  # pragma: no cover
        return "submit" in request.args
