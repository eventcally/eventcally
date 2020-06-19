from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.fields.html5 import DateTimeLocalField
from wtforms.validators import DataRequired, Optional

class CreateEventForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Create event"))
    name = StringField(lazy_gettext('Name'), validators=[DataRequired()])
    external_link = StringField(lazy_gettext('Link URL'), validators=[Optional()])
    ticket_link = StringField(lazy_gettext('Ticket Link URL'), validators=[Optional()])
    description = TextAreaField(lazy_gettext('Description'), validators=[DataRequired()])
    start = DateTimeLocalField(lazy_gettext('Start'), format='%Y-%m-%dT%H:%M', validators=[DataRequired()])

    place_id = SelectField(lazy_gettext('Place'), validators=[DataRequired()], coerce=int)
    host_id = SelectField(lazy_gettext('Host'), validators=[DataRequired()], coerce=int)
