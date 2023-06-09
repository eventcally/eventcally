from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import Optional

from project.forms.common import distance_choices, weekday_choices
from project.forms.widgets import MultiCheckboxField


class PlanningForm(FlaskForm):
    class Meta:
        csrf = False

    date_from = HiddenField(lazy_gettext("From"), validators=[Optional()])
    date_to = HiddenField(lazy_gettext("to"), validators=[Optional()])
    category_id = MultiCheckboxField(
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
    exclude_recurring = BooleanField(
        lazy_gettext("Exclude recurring events"),
        validators=[Optional()],
    )
    postal_code = StringField(lazy_gettext("Postal code"), validators=[Optional()])
    expected_participants_min = IntegerField(
        lazy_gettext("Min. expected number of participants"),
        validators=[Optional()],
    )

    submit = SubmitField(lazy_gettext("Refresh"))
