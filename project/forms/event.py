from flask import request
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import Optional

from project.forms.common import distance_choices
from project.forms.widgets import CustomDateField


class FindEventForm(FlaskForm):
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
    tag = StringField(lazy_gettext("Tags"), validators=[Optional()])
    organizer_id = SelectField(
        lazy_gettext("Organizer"), validators=[Optional()], coerce=int
    )
    event_place_id = SelectField(
        lazy_gettext("Place"), validators=[Optional()], coerce=int
    )
    coordinate = HiddenField(validators=[Optional()])
    location_name = HiddenField(validators=[Optional()])
    location = SelectField(lazy_gettext("Location"), validators=[Optional()])
    distance = SelectField(
        lazy_gettext("Distance"),
        validators=[Optional()],
        coerce=int,
        choices=distance_choices,
    )
    postal_code = StringField(lazy_gettext("Postal code"), validators=[Optional()])
    exclude_recurring = BooleanField(
        lazy_gettext("Exclude recurring events"),
        validators=[Optional()],
    )
    created_at_from = CustomDateField(lazy_gettext("From"), validators=[Optional()])
    created_at_to = CustomDateField(
        lazy_gettext("to"), set_end_of_day=True, validators=[Optional()]
    )
    sort = SelectField(
        lazy_gettext("Sort"),
        choices=[
            (
                "start",
                lazy_gettext("Earliest start first"),
            ),
            (
                "-created_at",
                lazy_gettext("Newest first"),
            ),
            (
                "-last_modified_at",
                lazy_gettext("Last modified first"),
            ),
        ],
        default="start",
    )

    submit = SubmitField(lazy_gettext("Find events"))

    def is_submitted(self):  # pragma: no cover
        return "submit" in request.args
