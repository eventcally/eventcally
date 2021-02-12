from flask import request
from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import Optional

from project.forms.common import distance_choices
from project.forms.widgets import CustomDateField


class FindEventDateForm(FlaskForm):
    class Meta:
        csrf = False

    date_from = CustomDateField(lazy_gettext("From"), validators=[Optional()])
    date_to = CustomDateField(lazy_gettext("to"), validators=[Optional()])
    keyword = StringField(lazy_gettext("Keyword"), validators=[Optional()])
    category_id = SelectField(
        lazy_gettext("Category"), validators=[Optional()], coerce=int
    )
    coordinate = HiddenField(validators=[Optional()])
    location = StringField(lazy_gettext("Location"), validators=[Optional()])
    distance = SelectField(
        lazy_gettext("Distance"),
        validators=[Optional()],
        coerce=int,
        choices=distance_choices,
    )

    submit = SubmitField(lazy_gettext("Find"))

    def is_submitted(self):
        return "submit" in request.args
