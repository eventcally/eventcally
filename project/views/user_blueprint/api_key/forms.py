from flask_babel import lazy_gettext
from wtforms import StringField
from wtforms.validators import DataRequired

from project.modular.base_form import BaseCreateForm, BaseDeleteForm, BaseUpdateForm


class CreateForm(BaseCreateForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )


class UpdateForm(BaseUpdateForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )


class DeleteForm(BaseDeleteForm):
    confirmation_field_name = "name"
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
