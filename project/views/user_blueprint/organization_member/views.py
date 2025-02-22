from flask import flash, redirect, url_for
from flask_babel import gettext, lazy_gettext

from project.access import can_current_user_delete_member
from project.modular.base_views import BaseDeleteView
from project.views.user_blueprint.organization_member.forms import DeleteForm
from project.views.utils import flash_non_match_for_deletion


class DeleteView(BaseDeleteView):
    form_class = DeleteForm

    def get_title(self, **kwargs):
        return lazy_gettext("Leave organization")

    def get_instruction(self, **kwargs):
        member = kwargs.get("object")
        return lazy_gettext(
            "Do you want to leave organization %(name)s?", name=member.adminunit.name
        )

    def check_object_access(self, object):
        response = super().check_object_access(object)

        if response:  # pragma: no cover
            return response

        if not can_current_user_delete_member(object):
            flash(
                gettext("Last remaining administrator can not leave the organization."),
                "danger",
            )
            return redirect(url_for("manage_admin_unit.organization_members", id=id))

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.name.data,
            object.adminunit.name,
            gettext("Entered name does not match organization name"),
        )

    def get_success_text(self, object, form):
        return lazy_gettext("Organization successfully left")
