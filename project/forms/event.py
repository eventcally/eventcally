from flask import request
from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from wtforms import (
    SelectMultipleField,
    RadioField,
    StringField,
    SubmitField,
    TextAreaField,
    SelectField,
    BooleanField,
    IntegerField,
    FormField,
)
from wtforms.fields.html5 import EmailField, URLField
from wtforms.validators import DataRequired, Optional
from project.models import (
    EventPlace,
    EventTargetGroupOrigin,
    EventAttendanceMode,
    EventStatus,
    Location,
    EventOrganizer,
    Image,
)
from project.forms.common import event_rating_choices, Base64ImageForm
from project.forms.widgets import CustomDateTimeField, CustomDateField
from dateutil.relativedelta import relativedelta


class EventPlaceLocationForm(FlaskForm):
    street = StringField(lazy_gettext("Street"), validators=[Optional()])
    postalCode = StringField(lazy_gettext("Postal code"), validators=[Optional()])
    city = StringField(lazy_gettext("City"), validators=[Optional()])


class EventPlaceForm(FlaskForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[Optional()],
    )
    location = FormField(EventPlaceLocationForm, default=lambda: Location())

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
        validators=[Optional()],
    )
    url = URLField(lazy_gettext("Link URL"), validators=[Optional()])
    email = EmailField(lazy_gettext("Email"), validators=[Optional()])
    phone = StringField(lazy_gettext("Phone"), validators=[Optional()])
    fax = StringField(lazy_gettext("Fax"), validators=[Optional()])


class SharedEventForm(FlaskForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        description=lazy_gettext("Enter a short, meaningful name for the event."),
    )
    start = CustomDateTimeField(
        lazy_gettext("Start"),
        validators=[DataRequired()],
        description=lazy_gettext(
            "Indicate when the event will take place.  If the event takes place regularly, enter when the first date will begin."
        ),
    )
    end = CustomDateTimeField(
        lazy_gettext("End"),
        validators=[Optional()],
        description=lazy_gettext(
            "Indicate when the event will end. An event can last a maximum of 24 hours. If the event takes place regularly, enter when the first date will end."
        ),
    )
    recurrence_rule = TextAreaField(
        lazy_gettext("Recurrence rule"),
        validators=[Optional()],
        description=lazy_gettext("Enter if the event takes place regularly."),
    )
    description = TextAreaField(
        lazy_gettext("Description"),
        validators=[Optional()],
        description=lazy_gettext("Add an description of the event."),
    )
    external_link = URLField(
        lazy_gettext("Link URL"),
        validators=[Optional()],
        description=lazy_gettext(
            "Enter a link to an external website containing more information about the event."
        ),
    )
    ticket_link = StringField(
        lazy_gettext("Ticket Link URL"),
        validators=[Optional()],
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

    def validate(self):
        if not super().validate():
            return False
        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                msg = gettext("The start must be before the end.")
                self.start.errors.append(msg)
                return False

            max_end = self.start.data + relativedelta(days=1)
            if self.end.data > max_end:
                msg = gettext("An event can last a maximum of 24 hours.")
                self.end.errors.append(msg)
                return False
        return True


class BaseEventForm(SharedEventForm):
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
            "Choose how relevant the event is to your organization."
        ),
    )


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

    submit = SubmitField(lazy_gettext("Create event"))

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
            field.populate_obj(obj, name)

    def validate(self):
        if not super(BaseEventForm, self).validate():
            return False
        if self.event_place_id.data == 0 and not self.new_event_place.form.name.data:
            msg = gettext("Select existing place or enter new place")
            self.event_place_id.errors.append(msg)
            self.new_event_place.form.name.errors.append(msg)
            return False
        if self.organizer_id.data == 0 and not self.new_organizer.form.name.data:
            msg = gettext("Select existing organizer or enter new organizer")
            self.organizer_id.errors.append(msg)
            self.new_organizer.form.name.errors.append(msg)
            return False
        return True


class UpdateEventForm(BaseEventForm):
    event_place_id = SelectField(
        lazy_gettext("Place"),
        validators=[DataRequired()],
        coerce=int,
        description=lazy_gettext(
            "Choose where the event takes place. You can add and modify places at Manage > Places."
        ),
    )
    organizer_id = SelectField(
        lazy_gettext("Organizer"),
        validators=[DataRequired()],
        coerce=int,
        description=lazy_gettext(
            "Select the organizer. You can add and modify organizers at Manage > Organizers."
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

    submit = SubmitField(lazy_gettext("Update event"))

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "photo" and not obj.photo:
                obj.photo = Image()
            field.populate_obj(obj, name)


class DeleteEventForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete event"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])


class FindEventForm(FlaskForm):
    class Meta:
        csrf = False

    date_from = CustomDateField(lazy_gettext("From"), validators=[Optional()])
    date_to = CustomDateField(lazy_gettext("to"), validators=[Optional()])
    keyword = StringField(lazy_gettext("Keyword"), validators=[Optional()])
    category_id = SelectField(
        lazy_gettext("Category"), validators=[Optional()], coerce=int
    )
    organizer_id = SelectField(
        lazy_gettext("Organizer"), validators=[Optional()], coerce=int
    )

    submit = SubmitField(lazy_gettext("Find events"))

    def is_submitted(self):
        return "submit" in request.args
