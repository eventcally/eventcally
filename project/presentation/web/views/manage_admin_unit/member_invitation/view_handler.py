from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.member_invitation.views import (
    CreateView,
    ListView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list and the form are Vue pages (`/bff/manage`); changing the roles
    and revoking are modals of the list."""

    model_name = "organization_member_invitation"
    model_name_plural = "organization_member_invitations"
    display_name = "Organization member invitation"
    display_name_plural = "Organization member invitations"
    create_view_class = CreateView
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
