from flask import request
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import Optional

from project.forms.common import distance_choices
from project.forms.widgets import CustomDateField


class FindEventDateForm(FlaskForm):
    class Meta:
        csrf = False

    date_from = CustomDateField(lazy_gettext("From"), validators=[Optional()])
    date_to = CustomDateField(
        lazy_gettext("to"), set_end_of_day=True, validators=[Optional()]
    )
    keyword = StringField(lazy_gettext("Keyword"), validators=[Optional()])
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
    event_list_id = HiddenField(validators=[Optional()])
    organization_id = HiddenField(validators=[Optional()])
    organizer_id = HiddenField(validators=[Optional()])
    s_ft = HiddenField(validators=[Optional()])
    s_bg = HiddenField(validators=[Optional()])
    s_pr = HiddenField(validators=[Optional()])
    s_li = HiddenField(validators=[Optional()])

    submit = SubmitField(lazy_gettext("Find"))

    def is_submitted(self):
        return "submit" in request.args
