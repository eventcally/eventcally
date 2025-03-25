from flask import flash, redirect, url_for
from flask_babel import gettext, lazy_gettext

from project import db
from project.modular.base_views import BaseObjectFormView
from project.views.user_blueprint.organization_invitation.forms import NegotiateForm
from project.views.utils import handle_db_error


class NegotiateView(BaseObjectFormView):
    form_class = NegotiateForm
    template_file_name = "form_layout.html"

    def get_instruction(self, **kwargs):
        invitation = kwargs.get("object")
        return lazy_gettext(
            "%(name)s invited you to create an organization.",
            name=invitation.adminunit.name,
        )

    @handle_db_error
    def dispatch_validated_form(self, form, object, **kwargs):
        invitation = object

        if form.accept.data:
            return redirect(
                url_for("manage.organization_create", invitation_id=invitation.id)
            )

        db.session.delete(invitation)
        db.session.commit()
        flash(gettext("Invitation successfully declined"), "success")
        return redirect(self.handler.get_list_url())
