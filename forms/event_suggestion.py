from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.fields.html5 import DateTimeLocalField
from wtforms.validators import DataRequired, Optional

class CreateEventSuggestionForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Suggest event"))
    event_name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    description = TextAreaField(lazy_gettext('Description'), validators=[DataRequired()])
    start = DateTimeLocalField(lazy_gettext('Start'), format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    external_link = StringField(lazy_gettext('Link URL'), validators=[Optional()])

    place_name = StringField(lazy_gettext('Event place'), validators=[DataRequired()])
    place_street = StringField(lazy_gettext('Street'), validators=[Optional()])
    place_postalCode = StringField(lazy_gettext('Postal code'), validators=[DataRequired()])
    place_city = StringField(lazy_gettext('City'), validators=[DataRequired()])

    host_name = StringField(lazy_gettext('Event host'), validators=[DataRequired()])
    contact_name = StringField(lazy_gettext('Contact name'), validators=[DataRequired()])
    contact_email = StringField(lazy_gettext('Contact email'), validators=[DataRequired()])
