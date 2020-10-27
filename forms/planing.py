from flask import request
from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import HiddenField, SelectMultipleField, FieldList, RadioField, DateTimeField, StringField, SubmitField, TextAreaField, SelectField, BooleanField, IntegerField, FormField
from wtforms.fields.html5 import DateTimeLocalField, EmailField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import html_params, HTMLString
from models import EventPlace, EventTargetGroupOrigin, EventAttendanceMode, EventStatus, Location, EventOrganizer, EventRejectionReason, EventReviewStatus
from .common import event_rating_choices, weekday_choices, distance_choices
from .widgets import CustomDateField, MultiCheckboxField

class PlaningForm(FlaskForm):
    class Meta:
        csrf = False

    date_from = CustomDateField(lazy_gettext('From'), validators=[Optional()])
    date_to = CustomDateField(lazy_gettext('to'), validators=[Optional()])
    category_id = SelectField(lazy_gettext('Category'), validators=[Optional()], coerce=int)
    coordinate = HiddenField(validators=[Optional()])
    location = StringField(lazy_gettext('Location'), validators=[Optional()])
    distance = SelectField(lazy_gettext('Distance'), validators=[Optional()], coerce=int, choices=distance_choices)
    weekday = MultiCheckboxField(lazy_gettext('Weekdays'), validators=[Optional()], coerce=int, choices=weekday_choices)

    submit = SubmitField(lazy_gettext("Find"))

    def is_submitted(self):
        return 'submit' in request.args