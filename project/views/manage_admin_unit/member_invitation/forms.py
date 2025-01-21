from flask_babel import lazy_gettext
from wtforms import EmailField
from wtforms.validators import DataRequired, Length

from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseCreateForm, BaseUpdateForm


class SharedFormMixin(object):
    roles = MultiCheckboxField(
        lazy_gettext("Roles"),
        render_kw={"ri": "multicheckbox"},
    )

    def populate_obj(self, obj):
        super().populate_obj(obj)

        obj.roles = ",".join(self.roles.data)


class CreateForm(SharedFormMixin, BaseCreateForm):
    email = EmailField(
        lazy_gettext("Email"),
        validators=[DataRequired(), Length(max=255)],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.move_field_to_top("email")


class UpdateForm(SharedFormMixin, BaseUpdateForm):
    pass
