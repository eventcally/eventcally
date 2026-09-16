from flask_babel import lazy_gettext
from wtforms import EmailField
from wtforms.validators import DataRequired, Length

from project.application.commands import (
    InviteUserToOrganizationCommand,
    UpdateMemberInvitationCommand,
)
from project.domain.types import ObjectId
from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseCreateForm, BaseUpdateForm


class SharedFormMixin(object):
    roles = MultiCheckboxField(
        lazy_gettext("Roles"),
        render_kw={"ri": "multicheckbox"},
    )


class CreateForm(SharedFormMixin, BaseCreateForm):
    email = EmailField(
        lazy_gettext("Email"),
        validators=[DataRequired(), Length(max=255)],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.move_field_to_top("email")

    def create_create_command(
        self, *, admin_unit_id: ObjectId
    ) -> InviteUserToOrganizationCommand:
        return InviteUserToOrganizationCommand(
            actor=self.get_current_actor(),
            admin_unit_id=admin_unit_id,
            email=self.email.data,
            roles=self.roles.data,
        )


class UpdateForm(SharedFormMixin, BaseUpdateForm):
    def create_update_command(self, id: ObjectId) -> UpdateMemberInvitationCommand:
        return UpdateMemberInvitationCommand(
            actor=self.get_current_actor(),
            id=id,
            roles=self.roles.data,
        )
