from flask import flash, redirect, url_for
from flask_babel import gettext, lazy_gettext
from flask_security import current_user

from project.application.commands import (
    AcceptMemberInvitationCommand,
    DeclineMemberInvitationCommand,
)
from project.modular.base_views import BaseObjectFormView
from project.views.user_blueprint.organization_member_invitation.forms import (
    NegotiateForm,
)
from project.views.utils import handle_base_error


class NegotiateView(BaseObjectFormView):
    form_class = NegotiateForm
    template_file_name = "form_layout.html"

    def get_instruction(self, **kwargs):
        invitation = kwargs.get("object")
        return lazy_gettext(
            "Would you like to accept the invitation from %(name)s?",
            name=invitation.admin_unit.name,
        )

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        invitation = object
        actor = self.app_context_provider.get_current_actor()

        if form.accept.data:
            if current_user.deletion_requested_at:  # pragma: no cover
                flash(gettext("Your account is scheduled for deletion."), "danger")
                return redirect(url_for("main.profile"))

            self.message_bus.handle_command(
                AcceptMemberInvitationCommand(id=invitation.id, actor=actor)
            )
            message = gettext("Invitation successfully accepted")
            url = url_for("main.manage_admin_unit", id=invitation.admin_unit_id)
        else:
            self.message_bus.handle_command(
                DeclineMemberInvitationCommand(id=invitation.id, actor=actor)
            )
            message = gettext("Invitation successfully declined")
            url = url_for("main.manage")

        flash(message, "success")
        return redirect(url)
