from flask_babel import lazy_gettext
from wtforms import SubmitField
from wtforms.validators import DataRequired

from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseForm, BaseUpdateForm


class InstallAppForm(BaseForm):
    permissions = MultiCheckboxField(
        lazy_gettext("Permissions"),
        validators=[DataRequired()],
        render_kw={"ri": "multicheckbox", "disabled": True},
    )
    submit = SubmitField(lazy_gettext("Install"))


class AcceptPermissionsForm(BaseUpdateForm):
    permissions = MultiCheckboxField(
        lazy_gettext("New permissions"),
        validators=[DataRequired()],
        render_kw={"ri": "multicheckbox", "disabled": True},
    )
