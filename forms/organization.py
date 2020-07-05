from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, DecimalField, TextAreaField, FormField, SelectField
from wtforms.validators import DataRequired, Optional
import decimal

class OrganizationLocationForm(FlaskForm):
    street = StringField(lazy_gettext('Street'), validators=[Optional()])
    postalCode = StringField(lazy_gettext('Postal code'), validators=[DataRequired()])
    city = StringField(lazy_gettext('City'), validators=[DataRequired()])
    state = StringField(lazy_gettext('State'), validators=[Optional()])
    latitude = DecimalField(lazy_gettext('Latitude'), places=16, validators=[Optional()])
    longitude = DecimalField(lazy_gettext('Longitude'), places=16, validators=[Optional()])

class BaseOrganizationForm(FlaskForm):
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    url = StringField(lazy_gettext('Link URL'), validators=[Optional()])
    logo_file = FileField(lazy_gettext('Logo'), validators=[FileAllowed(['jpg', 'jpeg', 'png'], lazy_gettext('Images only!'))])
    legal_name = TextAreaField(lazy_gettext('Legal name'), validators=[Optional()])
    location = FormField(OrganizationLocationForm)

class CreateOrganizationForm(BaseOrganizationForm):
    submit = SubmitField(lazy_gettext("Create organization"))
    admin_unit_id = SelectField(lazy_gettext('Admin unit'), validators=[DataRequired()], coerce=int)

class UpdateOrganizationForm(BaseOrganizationForm):
    submit = SubmitField(lazy_gettext("Update organization"))