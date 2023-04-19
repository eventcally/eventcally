from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, SubmitField
from wtforms.validators import Optional

from project.forms.common import distance_choices, weekday_choices
from project.forms.widgets import CustomDateField, MultiCheckboxField


class PlaningForm(FlaskForm):
    class Meta:
        csrf = False

    date_from = CustomDateField(lazy_gettext("From"), validators=[Optional()])
    date_to = CustomDateField(
        lazy_gettext("to"), set_end_of_day=True, validators=[Optional()]
    )
    category_id = SelectField(
        lazy_gettext("Category"), validators=[Optional()], coerce=int
    )
    coordinate = HiddenField(validators=[Optional()])
    location = SelectField(lazy_gettext("Location"), validators=[Optional()])
    distance = SelectField(
        lazy_gettext("Distance"),
        validators=[Optional()],
        coerce=int,
        choices=distance_choices,
    )
    weekday = MultiCheckboxField(
        lazy_gettext("Weekdays"),
        validators=[Optional()],
        coerce=int,
        choices=weekday_choices,
    )

    submit = SubmitField(lazy_gettext("Find"))
