from flask_babel import lazy_gettext
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from project.presentation.web.modular.base_form import BaseForm


class DeleteEventOrganizerForm(BaseForm):
    submit = SubmitField(lazy_gettext("Delete organizer"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])
