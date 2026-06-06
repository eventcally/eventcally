from flask_babel import lazy_gettext
from wtforms import SubmitField
from wtforms.validators import DataRequired

from project.application.commands.install_app_command import InstallAppCommand
from project.application.commands.update_app_installation_permissions_command import (
    UpdateAppInstallationPermissionsCommand,
)
from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseForm, BaseUpdateForm


class InstallAppForm(BaseForm):
    permissions = MultiCheckboxField(
        lazy_gettext("Permissions"),
        validators=[DataRequired()],
        render_kw={"ri": "multicheckbox", "disabled": True},
    )
    submit = SubmitField(lazy_gettext("Install"))

    def create_create_command(
        self, admin_unit_id: int, app_id: int
    ) -> InstallAppCommand:
        return InstallAppCommand.model_construct(
            admin_unit_id=admin_unit_id,
            app_id=app_id,
        )


class AcceptPermissionsForm(BaseUpdateForm):
    permissions = MultiCheckboxField(
        lazy_gettext("New permissions"),
        validators=[DataRequired()],
        render_kw={"ri": "multicheckbox", "disabled": True},
    )

    def create_update_command(
        self, app_installation_id: int
    ) -> UpdateAppInstallationPermissionsCommand:
        return UpdateAppInstallationPermissionsCommand.model_construct(
            id=app_installation_id,
            permissions=self.permissions.data,
        )
