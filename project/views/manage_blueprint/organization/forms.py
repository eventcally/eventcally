from flask_babel import lazy_gettext
from wtforms import FormField
from wtforms.fields import BooleanField
from wtforms.validators import Optional

from project.application.commands import CreateOrganizationCommand
from project.models import AdminUnitRelation
from project.modular.base_form import BaseCreateForm, BaseForm
from project.views.manage_admin_unit.admin_unit.forms import AdminUnitFormMixin


class AdminUnitRelationForm(BaseForm):
    verify = BooleanField(
        lazy_gettext("Verify new organization"),
        description=lazy_gettext(
            "If set, events of the new organization are publicly visible."
        ),
        validators=[Optional()],
        render_kw={"ri": "checkbox"},
    )
    auto_verify_event_reference_requests = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        description=lazy_gettext(
            "If set, all upcoming reference requests of the new organization are verified automatically."
        ),
        validators=[Optional()],
        render_kw={"ri": "checkbox"},
    )


class CreateForm(BaseCreateForm, AdminUnitFormMixin):
    embedded_relation = FormField(
        AdminUnitRelationForm, default=lambda: AdminUnitRelation()
    )

    def create_create_command(
        self, invitation=None, current_admin_unit=None, embedded_relation_enabled=False
    ) -> CreateOrganizationCommand:
        kwargs = dict(
            actor=self.get_current_actor(),
            name=self.name.data,
            short_name=self.short_name.data,
            description=self.description.data,
            location=self.location.form.create_create_command(),
            logo=self.logo.form.create_create_command(),
            url=self.additional_information.form.url.data,
            email=self.additional_information.form.email.data,
            phone=self.additional_information.form.phone.data,
            fax=self.additional_information.form.fax.data,
        )

        if invitation:
            kwargs["invitation_id"] = invitation.id
        elif embedded_relation_enabled and current_admin_unit:
            kwargs["current_admin_unit_id"] = current_admin_unit.id

            verify_field = getattr(self.embedded_relation.form, "verify", None)
            if verify_field is not None:
                kwargs["embedded_relation_verify"] = verify_field.data

            auto_verify_field = getattr(
                self.embedded_relation.form,
                "auto_verify_event_reference_requests",
                None,
            )
            if auto_verify_field is not None:
                kwargs["embedded_relation_auto_verify_event_reference_requests"] = (
                    auto_verify_field.data
                )

        return CreateOrganizationCommand(**kwargs)
