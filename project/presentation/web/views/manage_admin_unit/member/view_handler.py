from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.member.views import ListView


class ViewHandler(ManageAdminUnitChildViewHandler):
    """A shell: the list is a Vue page (`/bff/manage`); changing the roles and removing
    a member are modals of the list, inviting is the member invitation form."""

    model_name = "organization_member"
    model_name_plural = "organization_members"
    display_name = "Organization member"
    display_name_plural = "Organization members"
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
