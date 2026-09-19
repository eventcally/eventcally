from flask_babel import lazy_gettext
from wtforms import BooleanField, EmailField, StringField
from wtforms.validators import DataRequired, Length

from project.application.commands import (
    InviteOrganizationCommand,
    UpdateOrganizationInvitationCommand,
)
from project.domain.types import ObjectId, unset
from project.modular.base_form import BaseCreateForm, BaseUpdateForm


class SharedFormMixin(object):
    admin_unit_name = StringField(
        lazy_gettext("New organization's name"),
        validators=[DataRequired(), Length(max=255)],
    )
    relation_verify = BooleanField(
        lazy_gettext("Verify new organization"),
        description=lazy_gettext(
            "If set, events of the new organization are publicly visible."
        ),
        render_kw={"ri": "switch"},
    )
    relation_auto_verify_event_reference_requests = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        description=lazy_gettext(
            "If set, all upcoming reference requests of the new organization are verified automatically."
        ),
        render_kw={"ri": "switch"},
    )


class CreateForm(BaseCreateForm, SharedFormMixin):
    email = EmailField(
        lazy_gettext("Email"),
        description=lazy_gettext("The invitation will be sent to this email address."),
        validators=[DataRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.move_field_to_top("email")

    def create_create_command(
        self, *, admin_unit_id: ObjectId
    ) -> InviteOrganizationCommand:
        # relation_verify is removed from the form entirely (see
        # SharedFormViewMixin.create_form) when the admin unit lacks
        # can_verify_other — the invitation is then created without it, same
        # as the old CRUD path leaving the model field at its default.
        relation_verify = getattr(self, "relation_verify", None)

        return InviteOrganizationCommand(
            actor=self.get_current_actor(),
            admin_unit_id=admin_unit_id,
            email=self.email.data,
            admin_unit_name=self.admin_unit_name.data,
            relation_auto_verify_event_reference_requests=(
                self.relation_auto_verify_event_reference_requests.data
            ),
            relation_verify=relation_verify.data if relation_verify else False,
        )


class UpdateForm(BaseUpdateForm, SharedFormMixin):
    def create_update_command(
        self, id: ObjectId
    ) -> UpdateOrganizationInvitationCommand:
        relation_verify = getattr(self, "relation_verify", None)

        return UpdateOrganizationInvitationCommand(
            actor=self.get_current_actor(),
            id=id,
            admin_unit_name=self.admin_unit_name.data,
            relation_auto_verify_event_reference_requests=(
                self.relation_auto_verify_event_reference_requests.data
            ),
            relation_verify=relation_verify.data if relation_verify else unset,
        )
