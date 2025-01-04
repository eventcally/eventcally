from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class CreateEventReferenceRequestForm(FlaskForm):
    admin_unit_id = SelectField(
        lazy_gettext("Organization"), validators=[DataRequired()], coerce=int
    )
    submit = SubmitField(lazy_gettext("Save request"))
