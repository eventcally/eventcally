from flask import flash, redirect, url_for
from flask_babel import gettext, lazy_gettext
from flask_security import current_user

from project import db
from project.modular.base_views import BaseObjectFormView
from project.services.admin_unit import add_user_to_admin_unit_with_roles
from project.views.user_blueprint.organization_member_invitation.forms import (
    NegotiateForm,
)
from project.views.utils import handle_db_error


class NegotiateView(BaseObjectFormView):
    form_class = NegotiateForm
    template_file_name = "form_layout.html"

    def get_instruction(self, **kwargs):
        invitation = kwargs.get("object")
        return lazy_gettext(
            "Would you like to accept the invitation from %(name)s?",
            name=invitation.admin_unit.name,
        )

    @handle_db_error
    def dispatch_validated_form(self, form, object, **kwargs):
        invitation = object

        if form.accept.data:
            if current_user.deletion_requested_at:  # pragma: no cover
                flash(gettext("Your account is scheduled for deletion."), "danger")
                return redirect(url_for("profile"))

            message = gettext("Invitation successfully accepted")
            roles = invitation.roles.split(",")
            add_user_to_admin_unit_with_roles(
                current_user, invitation.admin_unit, roles
            )
            url = url_for("manage_admin_unit", id=invitation.admin_unit_id)
        else:
            message = gettext("Invitation successfully declined")
            url = url_for("manage")

        db.session.delete(invitation)
        db.session.commit()
        flash(message, "success")
        return redirect(url)
