from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

from project.forms.common import event_rating_choices


class CreateEventReferenceForm(FlaskForm):
    admin_unit_id = SelectField(
        lazy_gettext("Organization"), validators=[DataRequired()], coerce=int
    )
    rating = SelectField(
        lazy_gettext("Rating"),
        default=50,
        coerce=int,
        choices=event_rating_choices,
        description=lazy_gettext(
            "Choose how relevant the event is to your organization. The value is not visible and is used for sorting."
        ),
    )
    submit = SubmitField(lazy_gettext("Save reference"))
