from flask_babel import lazy_gettext

from project.application.commands import ChangeOrganizationMemberRolesCommand
from project.domain.types import ObjectId
from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseUpdateForm


class UpdateForm(BaseUpdateForm):
    role_names = MultiCheckboxField(
        lazy_gettext("Roles"),
        render_kw={"ri": "multicheckbox"},
    )

    def create_update_command(
        self, id: ObjectId
    ) -> ChangeOrganizationMemberRolesCommand:
        return ChangeOrganizationMemberRolesCommand(
            actor=self.get_current_actor(),
            id=id,
            roles=self.role_names.data,
        )
