from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import DecimalField, RadioField, DateTimeField, StringField, SubmitField, TextAreaField, SelectField, BooleanField, IntegerField, FormField
from wtforms.fields.html5 import DateTimeLocalField, EmailField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import html_params, HTMLString
import decimal
from models import Location

class EventPlaceLocationForm(FlaskForm):
    street = StringField(lazy_gettext('Street'), validators=[Optional()])
    postalCode = StringField(lazy_gettext('Postal code'), validators=[Optional()])
    city = StringField(lazy_gettext('City'), validators=[Optional()])
    state = StringField(lazy_gettext('State'), validators=[Optional()])
    latitude = DecimalField(lazy_gettext('Latitude'), places=16, validators=[Optional()])
    longitude = DecimalField(lazy_gettext('Longitude'), places=16, validators=[Optional()])

class BaseEventPlaceForm(FlaskForm):
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    url = StringField(lazy_gettext('Link URL'), validators=[Optional()])
    photo_file = FileField(lazy_gettext('Photo'), validators=[FileAllowed(['jpg', 'jpeg', 'png'], lazy_gettext('Images only!'))])
    description = TextAreaField(lazy_gettext('Description'), validators=[Optional()])
    location = FormField(EventPlaceLocationForm)

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'location' and not obj.location:
                obj.location = Location()
            field.populate_obj(obj, name)

class CreateEventPlaceForm(BaseEventPlaceForm):
    public = BooleanField(lazy_gettext('Other organizers can use this location'), default="checked", render_kw ={'checked':''}, validators=[Optional()])
    submit = SubmitField(lazy_gettext("Create place"))

class UpdateEventPlaceForm(BaseEventPlaceForm):
    public = BooleanField(lazy_gettext('Other organizers can use this location'), validators=[Optional()])
    submit = SubmitField(lazy_gettext("Update place"))

class FindEventPlaceForm(FlaskForm):
    class Meta:
        csrf = False
    submit = SubmitField(lazy_gettext("Find places"))
    organizer_id = SelectField(lazy_gettext('Organizer'), validators=[DataRequired()], coerce=int)
