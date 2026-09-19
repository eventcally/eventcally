from flask import flash, redirect, url_for
from flask_babel import gettext, lazy_gettext

from project.application.commands import DeclineOrganizationInvitationCommand
from project.modular.base_views import BaseObjectFormView
from project.views.user_blueprint.organization_invitation.forms import NegotiateForm
from project.views.utils import handle_base_error


class NegotiateView(BaseObjectFormView):
    form_class = NegotiateForm
    template_file_name = "form_layout.html"

    def get_instruction(self, **kwargs):
        invitation = kwargs.get("object")
        return lazy_gettext(
            "%(name)s invited you to create an organization.",
            name=invitation.admin_unit.name,
        )

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        invitation = object

        if form.accept.data:
            return redirect(
                url_for("manage.organization_create", invitation_id=invitation.id)
            )

        cmd = DeclineOrganizationInvitationCommand(
            id=invitation.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        flash(gettext("Invitation successfully declined"), "success")
        return redirect(self.handler.get_list_url())
