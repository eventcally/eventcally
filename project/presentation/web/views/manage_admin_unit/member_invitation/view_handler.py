from project.application.queries import (
    GetOrganizationMemberInvitationQuery,
    ListOrganizationMemberInvitationsQuery,
)
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.modular.base_form import BaseDeleteForm
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.member_invitation.displays import (
    ListDisplay,
    UpdateDisplay,
)
from project.presentation.web.views.manage_admin_unit.member_invitation.forms import (
    CreateForm,
    UpdateForm,
)
from project.presentation.web.views.manage_admin_unit.member_invitation.views import (
    CreateView,
    DeleteView,
    UpdateView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "organization_member_invitation"
    model_name_plural = "organization_member_invitations"
    display_name = "Organization member invitation"
    display_name_plural = "Organization member invitations"
    create_form_class = CreateForm
    create_view_class = CreateView
    read_view_class = None
    update_form_class = UpdateForm
    update_view_class = UpdateView
    update_display_class = UpdateDisplay
    delete_form_class = BaseDeleteForm
    delete_view_class = DeleteView
    list_display_class = ListDisplay

    def create_list_query(self, form, page_request, **kwargs):
        return ListOrganizationMemberInvitationsQuery(
            admin_unit_id=current_admin_unit.id, page=page_request
        )

    def create_get_query(self, object_id):
        return GetOrganizationMemberInvitationQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
