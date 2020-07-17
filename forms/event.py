from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import DateTimeField, StringField, SubmitField, TextAreaField, SelectField, BooleanField, IntegerField, FormField
from wtforms.fields.html5 import DateTimeLocalField, EmailField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import html_params, HTMLString
from models import EventPlace, EventTargetGroupOrigin, EventAttendanceMode, EventStatus, Location, Place, EventOrganizer
from .widgets import CustomDateTimeField

class EventPlaceLocationForm(FlaskForm):
    street = StringField(lazy_gettext('Street'), validators=[Optional()])
    postalCode = StringField(lazy_gettext('Postal code'), validators=[Optional()])
    city = StringField(lazy_gettext('City'), validators=[Optional()])

class EventPlaceForm(FlaskForm):
    name = StringField(lazy_gettext('New place'), validators=[Optional()])
    location = FormField(EventPlaceLocationForm, default=lambda: Location())

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'location' and not obj.location:
                obj.location = Location()
            field.populate_obj(obj, name)

class EventOrganizerForm(FlaskForm):
    name = StringField(lazy_gettext('Organizator'), validators=[Optional()])
    org_name = StringField(lazy_gettext('Organization'), validators=[Optional()])
    url = StringField(lazy_gettext('Link URL'), validators=[Optional()])
    email = EmailField(lazy_gettext('Email'), validators=[Optional()])
    phone = StringField(lazy_gettext('Phone'), validators=[Optional()])

class CreateEventForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Create event"))
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    external_link = StringField(lazy_gettext('Link URL'), validators=[Optional()])
    ticket_link = StringField(lazy_gettext('Ticket Link URL'), validators=[Optional()])
    description = TextAreaField(lazy_gettext('Description'), validators=[DataRequired()])
    recurrence_rule = TextAreaField(lazy_gettext('Recurrence rule'), validators=[Optional()])
    start = CustomDateTimeField(lazy_gettext('Start'), validators=[DataRequired()])
    end = CustomDateTimeField(lazy_gettext('End'), validators=[Optional()])
    previous_start_date = CustomDateTimeField(lazy_gettext('Previous start date'), validators=[Optional()])
    tags = StringField(lazy_gettext('Tags'), validators=[Optional()])

    organizer = FormField(EventOrganizerForm, default=lambda: EventOrganizer())
    event_place = FormField(EventPlaceForm, default=lambda: EventPlace())

    place_id = SelectField(lazy_gettext('Existing place'), validators=[Optional()], coerce=int)
    host_id = SelectField(lazy_gettext('Host'), validators=[Optional()], coerce=int)
    category_id = SelectField(lazy_gettext('Category'), validators=[DataRequired()], coerce=int)
    admin_unit_id = SelectField(lazy_gettext('Admin unit'), validators=[DataRequired()], coerce=int)

    kid_friendly = BooleanField(lazy_gettext('Kid friendly'), validators=[Optional()])
    accessible_for_free = BooleanField(lazy_gettext('Accessible for free'), validators=[Optional()])
    age_from = IntegerField(lazy_gettext('Typical Age from'), validators=[Optional()])
    age_to = IntegerField(lazy_gettext('Typical Age to'), validators=[Optional()])

    target_group_origin = SelectField(lazy_gettext('Target group origin'), coerce=int, choices=[
        (int(EventTargetGroupOrigin.both), lazy_gettext('EventTargetGroupOrigin.both')),
        (int(EventTargetGroupOrigin.tourist), lazy_gettext('EventTargetGroupOrigin.tourist')),
        (int(EventTargetGroupOrigin.resident), lazy_gettext('EventTargetGroupOrigin.resident'))])

    attendance_mode = SelectField(lazy_gettext('Attendance mode'), coerce=int, choices=[
        (int(EventAttendanceMode.offline), lazy_gettext('EventAttendanceMode.offline')),
        (int(EventAttendanceMode.online), lazy_gettext('EventAttendanceMode.online')),
        (int(EventAttendanceMode.mixed), lazy_gettext('EventAttendanceMode.mixed'))])

    status = SelectField(lazy_gettext('Status'), coerce=int, choices=[
        (int(EventStatus.scheduled), lazy_gettext('EventStatus.scheduled')),
        (int(EventStatus.cancelled), lazy_gettext('EventStatus.cancelled')),
        (int(EventStatus.movedOnline), lazy_gettext('EventStatus.movedOnline')),
        (int(EventStatus.postponed), lazy_gettext('EventStatus.postponed')),
        (int(EventStatus.rescheduled), lazy_gettext('EventStatus.rescheduled'))])

    photo_file = FileField(lazy_gettext('Photo'), validators=[FileAllowed(['jpg', 'jpeg', 'png'], lazy_gettext('Images only!'))])

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'organizer' and not obj.organizer:
                obj.organizer = EventOrganizer()
            if name == 'event_place' and not obj.event_place:
                obj.event_place = EventPlace()
            field.populate_obj(obj, name)

    def validate(self):
        if not super(CreateEventForm, self).validate():
            return False
        if self.host_id.data == 0 and not self.organizer.form.name.data and not self.organizer.form.org_name.data:
            msg = gettext('Select existing host or enter organizer')
            self.host_id.errors.append(msg)
            self.organizer.form.name.errors.append(msg)
            self.organizer.form.org_name.errors.append(msg)
            return False
        if self.place_id.data == 0 and not self.event_place.form.name.data:
            msg = gettext('Select existing place or enter new place')
            self.place_id.errors.append(msg)
            self.event_place.form.name.errors.append(msg)
            return False
        return True

class UpdateEventForm(CreateEventForm):
    submit = SubmitField(lazy_gettext("Update event"))

class DeleteEventForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete event"))
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])