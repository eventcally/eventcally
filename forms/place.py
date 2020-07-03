from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, DecimalField, TextAreaField, FormField
from wtforms.validators import DataRequired, Optional
import decimal

class PlaceLocationForm(FlaskForm):
    street = StringField(lazy_gettext('Street'), validators=[Optional()])
    postalCode = StringField(lazy_gettext('Postal code'), validators=[DataRequired()])
    city = StringField(lazy_gettext('City'), validators=[DataRequired()])
    state = StringField(lazy_gettext('State'), validators=[Optional()])
    latitude = DecimalField(lazy_gettext('Latitude'), places=16, validators=[Optional()])
    longitude = DecimalField(lazy_gettext('Longitude'), places=16, validators=[Optional()])

class CreatePlaceForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Create place"))

    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    url = StringField(lazy_gettext('Link URL'), validators=[Optional()])
    photo_file = FileField(lazy_gettext('Photo'), validators=[FileAllowed(['jpg', 'jpeg', 'png'], lazy_gettext('Images only!'))])
    description = TextAreaField(lazy_gettext('Description'), validators=[Optional()])
    location = FormField(PlaceLocationForm)

class UpdatePlaceForm(CreatePlaceForm):
    submit = SubmitField(lazy_gettext("Update place"))