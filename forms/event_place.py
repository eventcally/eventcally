from flask_babelex import lazy_gettext, gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import DecimalField, RadioField, DateTimeField, StringField, SubmitField, TextAreaField, SelectField, BooleanField, IntegerField, FormField
from wtforms.fields.html5 import DateTimeLocalField, EmailField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import html_params, HTMLString
import decimal
from models import Location, Image
from .common import BaseImageForm

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
    photo = FormField(BaseImageForm, lazy_gettext('Photo'), default=lambda: Image())
    description = TextAreaField(lazy_gettext('Description'), validators=[Optional()])
    location = FormField(EventPlaceLocationForm)

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'location' and not obj.location:
                obj.location = Location()
            elif name == 'photo' and not obj.photo:
                obj.photo = Image()
            field.populate_obj(obj, name)

class CreateEventPlaceForm(BaseEventPlaceForm):
    submit = SubmitField(lazy_gettext("Create place"))

class UpdateEventPlaceForm(BaseEventPlaceForm):
    submit = SubmitField(lazy_gettext("Update place"))

class DeleteEventPlaceForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete place"))
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])

class FindEventPlaceForm(FlaskForm):
    class Meta:
        csrf = False
    submit = SubmitField(lazy_gettext("Find places"))
