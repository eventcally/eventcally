from flask import flash, redirect, request, url_for
from flask_babel import gettext, lazy_gettext
from flask_security import current_user

from project.access import can_create_admin_unit, has_access
from project.models import AdminUnitInvitation
from project.modular.base_views import BaseCreateView
from project.utils import strings_are_equal_ignoring_case
from project.views.manage_blueprint.organization.forms import CreateForm
from project.views.utils import (
    flash_message,
    get_current_admin_unit,
    handle_base_error,
    permission_missing,
)


class CreateView(BaseCreateView):
    form_class = CreateForm

    def check_access(self, **kwargs):
        response = super().check_access(**kwargs)
        if response:  # pragma: no cover
            return response

        invitation = None

        invitation_id = (
            int(request.args.get("invitation_id"))
            if "invitation_id" in request.args
            else 0
        )
        if invitation_id > 0:
            invitation = AdminUnitInvitation.query.get_or_404(invitation_id)

            if not strings_are_equal_ignoring_case(
                invitation.email, current_user.email
            ):
                return permission_missing(url_for("main.manage_admin_units"))

        if not invitation:
            if not can_create_admin_unit():
                flash_message(
                    gettext(
                        "Organizations cannot currently be created. The project is in a closed test phase. If you are interested, you can contact us."
                    ),
                    url_for("main.contact"),
                    gettext("Contact"),
                    "danger",
                )
                return redirect(url_for("main.manage_admin_units"))

            if current_user.deletion_requested_at:  # pragma: no cover
                flash(gettext("Your account is scheduled for deletion."), "danger")
                return redirect(url_for("main.profile"))

        self.invitation = invitation
        self.current_admin_unit = get_current_admin_unit()
        self.embedded_relation_enabled = (
            not invitation
            and self.current_admin_unit
            and has_access(
                self.current_admin_unit, "outgoing_organization_relations:write"
            )
            and (
                self.current_admin_unit.can_verify_other
                or self.current_admin_unit.incoming_reference_requests_allowed
            )
        )

    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if self.embedded_relation_enabled:
            form.embedded_relation.label.text = lazy_gettext(
                "Relation to %(admin_unit_name)s",
                admin_unit_name=self.current_admin_unit.name,
            )

            if not self.current_admin_unit.can_verify_other:
                del form.embedded_relation.form.verify
            elif not form.is_submitted():
                form.embedded_relation.form.verify.data = True

            if not self.current_admin_unit.incoming_reference_requests_allowed:
                del form.embedded_relation.form.auto_verify_event_reference_requests

        else:
            del form.embedded_relation

        if self.invitation and not form.is_submitted():
            form.name.data = self.invitation.admin_unit_name

        return form

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = form.create_create_command(
            invitation=self.invitation,
            current_admin_unit=self.current_admin_unit,
            embedded_relation_enabled=self.embedded_relation_enabled,
        )
        cmd_result = self.message_bus.handle_command(cmd)

        if not cmd_result.verified:
            flash(
                gettext(
                    "The organization is not verified. Events are therefore not publicly visible."
                ),
                "warning",
            )

        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))

    def get_redirect_url(self, object, **kwargs):
        cmd_result = object

        if cmd_result.verified:
            return url_for("main.manage_admin_unit", id=cmd_result.id)

        return url_for(
            "manage_admin_unit.outgoing_organization_verification_requests",
            id=cmd_result.id,
        )
