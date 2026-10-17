from flask import url_for

from project.application.queries import (
    GetOrganizationMemberQuery,
    ListOrganizationMembersQuery,
)
from project.modular.base_form import BaseDeleteForm
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.member.displays import ListDisplay, UpdateDisplay
from project.views.manage_admin_unit.member.forms import UpdateForm
from project.views.manage_admin_unit.member.views import DeleteView, UpdateView
from project.views.utils import current_admin_unit


class ViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "organization_member"
    model_name_plural = "organization_members"
    display_name = "Organization member"
    display_name_plural = "Organization members"
    create_view_class = None
    read_view_class = None
    update_form_class = UpdateForm
    update_view_class = UpdateView
    update_display_class = UpdateDisplay
    delete_form_class = BaseDeleteForm
    delete_view_class = DeleteView
    list_display_class = ListDisplay

    def create_list_query(self, form, page_request, **kwargs):
        return ListOrganizationMembersQuery(
            admin_unit_id=current_admin_unit.id, page=page_request
        )

    def create_get_query(self, object_id):
        return GetOrganizationMemberQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `AdminUnitMember.__str__` (the user's email).
        return object.user.email

    def get_create_url(self, **kwargs):
        return url_for(
            "manage_admin_unit.organization_member_invitation_create",
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
