from flask_babel import lazy_gettext

from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseUpdateForm


class UpdateForm(BaseUpdateForm):
    role_names = MultiCheckboxField(
        lazy_gettext("Roles"),
        render_kw={"ri": "multicheckbox"},
    )
