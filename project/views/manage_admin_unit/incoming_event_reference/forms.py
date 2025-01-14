from flask_babel import lazy_gettext
from wtforms import SelectField, SubmitField

from project.forms.common import event_rating_choices
from project.modular.base_form import BaseForm


class BaseEventReferenceForm(BaseForm):
    rating = SelectField(
        lazy_gettext("Rating"),
        default=50,
        coerce=int,
        choices=event_rating_choices,
        description=lazy_gettext(
            "Choose how relevant the event is to your organization. The value is not visible and is used for sorting."
        ),
    )


class UpdateEventReferenceForm(BaseEventReferenceForm):
    submit = SubmitField(lazy_gettext("Update reference"))


class DeleteEventReferenceForm(BaseForm):
    submit = SubmitField(lazy_gettext("Delete reference"))
