from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, DecimalField, TextAreaField, FormField, SelectField
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import DataRequired, Optional, Regexp
import decimal
from models import Location

class AdminUnitLocationForm(FlaskForm):
    street = StringField(lazy_gettext('Street'), validators=[Optional()])
    postalCode = StringField(lazy_gettext('Postal code'), validators=[DataRequired()])
    city = StringField(lazy_gettext('City'), validators=[DataRequired()])
    state = StringField(lazy_gettext('State'), validators=[Optional()])
    latitude = DecimalField(lazy_gettext('Latitude'), places=16, validators=[Optional()])
    longitude = DecimalField(lazy_gettext('Longitude'), places=16, validators=[Optional()])

class BaseAdminUnitForm(FlaskForm):
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    short_name = StringField(lazy_gettext('Short name'), description=lazy_gettext('The short name is used to create a unique identifier for your events'), validators=[DataRequired(), Regexp('^\w+$', message=lazy_gettext("Short name must contain only letters numbers or underscore"))])
    url = StringField(lazy_gettext('Link URL'), validators=[Optional()])
    email = EmailField(lazy_gettext('Email'), validators=[Optional()])
    phone = TelField(lazy_gettext('Phone'), validators=[Optional()])
    fax = TelField(lazy_gettext('Fax'), validators=[Optional()])
    logo_file = FileField(lazy_gettext('Logo'), validators=[FileAllowed(['jpg', 'jpeg', 'png'], lazy_gettext('Images only!'))])
    location = FormField(AdminUnitLocationForm, default=lambda: Location())

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == 'location' and not obj.location:
                obj.location = Location()
            field.populate_obj(obj, name)

class CreateAdminUnitForm(BaseAdminUnitForm):
    submit = SubmitField(lazy_gettext("Create admin unit"))

class UpdateAdminUnitForm(BaseAdminUnitForm):
    submit = SubmitField(lazy_gettext("Update admin unit"))