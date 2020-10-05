from flask import request
from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import FieldList, RadioField, DateTimeField, StringField, SubmitField, TextAreaField, SelectField, BooleanField, IntegerField, FormField
from wtforms.fields.html5 import DateTimeLocalField, EmailField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import html_params, HTMLString
from models import EventContact, EventPlace, EventTargetGroupOrigin, EventAttendanceMode, EventStatus, Location, EventOrganizer, EventRejectionReason, EventReviewStatus, Image
from .common import event_rating_choices, BaseImageForm
from .widgets import CustomDateTimeField, CustomDateField

class EventPlaceLocationForm(FlaskForm):
    street = StringField(lazy_gettext('Street'), validators=[Optional()])
    postalCode = StringField(lazy_gettext('Postal code'), validators=[Optional()])
    city = StringField(lazy_gettext('City'), validators=[Optional()])

class EventPlaceForm(FlaskForm):
    name = StringField(lazy_gettext('Name'), validators=[Optional()])
    location = FormField(EventPlaceLocationForm, default=lambda: Location())
    public = BooleanField(lazy_gettext('Other organizers can use this location'), default="checked", render_kw ={'checked':''}, validators=[Optional()])

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'location' and not obj.location:
                obj.location = Location()
            field.populate_obj(obj, name)

class EventOrganizerForm(FlaskForm):
    name = StringField(lazy_gettext('Organizator'), validators=[Optional()])
    url = StringField(lazy_gettext('Link URL'), validators=[Optional()])
    email = EmailField(lazy_gettext('Email'), validators=[Optional()])
    phone = StringField(lazy_gettext('Phone'), validators=[Optional()])
    fax = StringField(lazy_gettext('Fax'), validators=[Optional()])

class EventContactForm(FlaskForm):
    name = StringField(lazy_gettext('Name'), validators=[Optional()])
    email = EmailField(lazy_gettext('Email'), validators=[Optional()])
    phone = StringField(lazy_gettext('Phone'), validators=[Optional()])

class BaseEventForm(FlaskForm):
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    external_link = StringField(lazy_gettext('Link URL'), validators=[Optional()])
    ticket_link = StringField(lazy_gettext('Ticket Link URL'), validators=[Optional()])
    description = TextAreaField(lazy_gettext('Description'), validators=[DataRequired()])
    recurrence_rule = TextAreaField(lazy_gettext('Recurrence rule'), validators=[Optional()])
    start = CustomDateTimeField(lazy_gettext('Start'), validators=[DataRequired()])
    end = CustomDateTimeField(lazy_gettext('End'), validators=[Optional()])
    previous_start_date = CustomDateTimeField(lazy_gettext('Previous start date'), validators=[Optional()])
    tags = StringField(lazy_gettext('Tags'), validators=[Optional()])

    organizer_id = SelectField(lazy_gettext('Organizer'), validators=[DataRequired()], coerce=int)
    category_id = SelectField(lazy_gettext('Category'), validators=[DataRequired()], coerce=int)

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

    photo = FormField(BaseImageForm, lazy_gettext('Photo'), default=lambda: Image())
    rating = SelectField(lazy_gettext('Rating'), default=50, coerce=int, choices=event_rating_choices)

class CreateEventForm(BaseEventForm):
    event_place_choice = RadioField(lazy_gettext('Place'), choices=[(1,lazy_gettext('Select existing place')), (2,lazy_gettext('Enter new place'))], default=1, coerce=int)
    event_place_id = SelectField(lazy_gettext('Place'), validators=[Optional()], coerce=int)
    new_event_place = FormField(EventPlaceForm, default=lambda: EventPlace())

    contact = FieldList(FormField(EventContactForm, default=lambda: EventContact()), max_entries=1)

    submit = SubmitField(lazy_gettext("Create event"))

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'new_event_place':
                if self.event_place_choice.data != 2:
                    continue
                if not obj.event_place:
                    obj.event_place = EventPlace()
                field.populate_obj(obj, 'event_place')
            elif name == 'photo' and not obj.photo:
                obj.photo = Image()
            field.populate_obj(obj, name)

        if isinstance(obj.contact, list):
            obj.contact = obj.contact[0] if len(obj.contact) > 0 else None

    def validate(self):
        if not super(BaseEventForm, self).validate():
            return False
        if self.event_place_id.data == 0 and not self.new_event_place.form.name.data:
            msg = gettext('Select existing place or enter new place')
            self.event_place_id.errors.append(msg)
            self.new_event_place.form.name.errors.append(msg)
            return False
        return True

class UpdateEventForm(BaseEventForm):
    event_place_id = SelectField(lazy_gettext('Place'), validators=[DataRequired()], coerce=int)

    status = SelectField(lazy_gettext('Status'), coerce=int, choices=[
        (int(EventStatus.scheduled), lazy_gettext('EventStatus.scheduled')),
        (int(EventStatus.cancelled), lazy_gettext('EventStatus.cancelled')),
        (int(EventStatus.movedOnline), lazy_gettext('EventStatus.movedOnline')),
        (int(EventStatus.postponed), lazy_gettext('EventStatus.postponed')),
        (int(EventStatus.rescheduled), lazy_gettext('EventStatus.rescheduled'))])

    submit = SubmitField(lazy_gettext("Update event"))

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'photo' and not obj.photo:
                obj.photo = Image()
            field.populate_obj(obj, name)

class DeleteEventForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete event"))
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])

class ReviewEventForm(FlaskForm):
    review_status = SelectField(lazy_gettext('Review status'), coerce=int, choices=[
        (int(EventReviewStatus.inbox), lazy_gettext('EventReviewStatus.inbox')),
        (int(EventReviewStatus.verified), lazy_gettext('EventReviewStatus.verified')),
        (int(EventReviewStatus.rejected), lazy_gettext('EventReviewStatus.rejected'))])

    rejection_resaon = SelectField(lazy_gettext('Rejection reason'), coerce=int, choices=[
        (0, ''),
        (int(EventRejectionReason.duplicate), lazy_gettext('EventRejectionReason.duplicate')),
        (int(EventRejectionReason.untrustworthy), lazy_gettext('EventRejectionReason.untrustworthy')),
        (int(EventRejectionReason.illegal), lazy_gettext('EventRejectionReason.illegal'))])

    rating = SelectField(lazy_gettext('Rating'), default=50, coerce=int, choices=event_rating_choices)

    submit = SubmitField(lazy_gettext("Save review"))

class FindEventForm(FlaskForm):
    class Meta:
        csrf = False
    date_from = CustomDateField(lazy_gettext('From'), validators=[Optional()])
    date_to = CustomDateField(lazy_gettext('to'), validators=[Optional()])
    keyword = StringField(lazy_gettext('Keyword'), validators=[Optional()])

    organizer_id = SelectField(lazy_gettext('Organizer'), validators=[Optional()], coerce=int)

    submit = SubmitField(lazy_gettext("Find events"))

    def is_submitted(self):
        return 'submit' in request.args
