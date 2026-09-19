from flask_babel import lazy_gettext
from wtforms import BooleanField
from wtforms.validators import DataRequired

from project.application.commands import (
    CreateOrganizationRelationCommand,
    UpdateOrganizationRelationCommand,
)
from project.domain.types import unset
from project.modular.base_form import BaseCreateForm, BaseUpdateForm
from project.modular.fields import AjaxSelectField
from project.views.manage_admin_unit.ajax import OrganizationAjaxModelLoader


class SharedFormMixin(object):
    verify = BooleanField(
        lazy_gettext("Verify other organization"),
        description=lazy_gettext(
            "If set, events of the other organization are publicly visible."
        ),
        render_kw={"ri": "switch"},
    )
    auto_verify_event_reference_requests = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        description=lazy_gettext(
            "If set, all upcoming reference requests of the other organization are verified automatically."
        ),
        render_kw={"ri": "switch"},
    )


class CreateForm(BaseCreateForm, SharedFormMixin):
    target_admin_unit = AjaxSelectField(
        OrganizationAjaxModelLoader(),
        lazy_gettext("Other organization"),
        validators=[DataRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.move_field_to_top("target_admin_unit")

    def create_create_command(
        self, source_admin_unit_id: int
    ) -> CreateOrganizationRelationCommand:
        return CreateOrganizationRelationCommand(
            actor=self.get_current_actor(),
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=self.target_admin_unit.data.id,
            auto_verify_event_reference_requests=self.auto_verify_event_reference_requests.data,
            verify=self.verify.data if self.verify else False,
        )


class UpdateForm(BaseUpdateForm, SharedFormMixin):
    def create_update_command(
        self, organization_relation_id: int
    ) -> UpdateOrganizationRelationCommand:
        return UpdateOrganizationRelationCommand(
            actor=self.get_current_actor(),
            id=organization_relation_id,
            auto_verify_event_reference_requests=self.auto_verify_event_reference_requests.data,
            verify=self.verify.data if self.verify else unset,
        )
