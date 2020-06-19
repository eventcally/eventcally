from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.fields.html5 import DateTimeLocalField
from wtforms.validators import DataRequired, Optional

class CreateEventForm(FlaskForm):
    submit = SubmitField("Create event")
    name = StringField('Name', validators=[DataRequired()])
    external_link = StringField('Link URL', validators=[Optional()])
    ticket_link = StringField('Ticket Link URL', validators=[Optional()])
    description = TextAreaField('Description', validators=[DataRequired()])
    start = DateTimeLocalField('Start', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])

    place_id = SelectField('Place', validators=[DataRequired()], coerce=int)
    host_id = SelectField('Host', validators=[DataRequired()], coerce=int)
