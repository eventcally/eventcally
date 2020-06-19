from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.fields.html5 import DateTimeLocalField
from wtforms.validators import DataRequired, Optional

class CreateEventSuggestionForm(FlaskForm):
    submit = SubmitField("Suggest event")
    event_name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    start = DateTimeLocalField('Start', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    external_link = StringField('Link URL', validators=[Optional()])

    place_name = StringField('Event place', validators=[DataRequired()])
    place_street = StringField('Street', validators=[Optional()])
    place_postalCode = StringField('Postal code', validators=[DataRequired()])
    place_city = StringField('City', validators=[DataRequired()])

    host_name = StringField('Event host', validators=[DataRequired()])
    contact_name = StringField('Contact name', validators=[DataRequired()])
    contact_email = StringField('Contact email', validators=[DataRequired()])



