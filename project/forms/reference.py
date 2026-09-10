from flask_babel import lazy_gettext
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

from project.application.commands import CreateEventReferenceCommand
from project.forms.common import event_rating_choices
from project.modular.base_form import BaseForm


class CreateEventReferenceForm(BaseForm):
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

    def create_create_command(self, event_id: int) -> CreateEventReferenceCommand:
        return CreateEventReferenceCommand(
            actor=self.get_current_actor(),
            admin_unit_id=self.admin_unit_id.data,
            event_id=event_id,
            rating=self.rating.data,
        )
