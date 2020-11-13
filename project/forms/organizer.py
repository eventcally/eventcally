from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, DecimalField, TextAreaField, FormField, SelectField
from wtforms.fields.html5 import EmailField, TelField, URLField
from wtforms.validators import DataRequired, Optional, Regexp
import decimal
from project.models import Location, Image
from project.forms.common import FileImageForm

class OrganizerLocationForm(FlaskForm):
    street = StringField(lazy_gettext('Street'), validators=[Optional()])
    postalCode = StringField(lazy_gettext('Postal code'), validators=[Optional()])
    city = StringField(lazy_gettext('City'), validators=[Optional()])
    state = StringField(lazy_gettext('State'), validators=[Optional()])
    latitude = DecimalField(lazy_gettext('Latitude'), places=16, validators=[Optional()])
    longitude = DecimalField(lazy_gettext('Longitude'), places=16, validators=[Optional()])

class BaseOrganizerForm(FlaskForm):
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    url = URLField(lazy_gettext('Link URL'), validators=[Optional()])
    email = EmailField(lazy_gettext('Email'), validators=[Optional()])
    phone = TelField(lazy_gettext('Phone'), validators=[Optional()])
    fax = TelField(lazy_gettext('Fax'), validators=[Optional()])
    logo = FormField(FileImageForm, lazy_gettext('Logo'), default=lambda: Image())
    location = FormField(OrganizerLocationForm)

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'location' and not obj.location:
                obj.location = Location()
            elif name == 'logo' and not obj.logo:
                obj.logo = Image()
            field.populate_obj(obj, name)

class CreateOrganizerForm(BaseOrganizerForm):
    submit = SubmitField(lazy_gettext("Create organizer"))

class UpdateOrganizerForm(BaseOrganizerForm):
    submit = SubmitField(lazy_gettext("Update organizer"))

class DeleteOrganizerForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete organizer"))
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])