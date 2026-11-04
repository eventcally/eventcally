from project.application.queries import GetOrganizationInvitationQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.organization_invitation.views import (
    CreateView,
    ListView,
    UpdateView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list and the form are Vue pages (`/bff/manage`); revoking is a modal
    of the list."""

    model_name = "organization_invitation"
    model_name_plural = "organization_invitations"
    display_name = "Organization invitation"
    display_name_plural = "Organization invitations"
    create_view_class = CreateView
    read_view_class = None
    update_view_class = UpdateView
    delete_view_class = None
    list_view_class = ListView

    def create_get_query(self, object_id):
        return GetOrganizationInvitationQuery(id=object_id)


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
