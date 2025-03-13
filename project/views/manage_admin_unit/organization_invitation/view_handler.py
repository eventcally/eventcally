from project.models import AdminUnitInvitation
from project.modular.base_form import BaseDeleteForm
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.organization_invitation.displays import (
    ListDisplay,
    UpdateDisplay,
)
from project.views.manage_admin_unit.organization_invitation.forms import (
    CreateForm,
    UpdateForm,
)
from project.views.manage_admin_unit.organization_invitation.views import (
    CreateView,
    UpdateView,
)
from project.views.utils import manage_permission_required


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = AdminUnitInvitation
    create_decorators = [manage_permission_required("admin_unit:update")]
    create_form_class = CreateForm
    create_view_class = CreateView
    read_view_class = None
    update_decorators = [manage_permission_required("admin_unit:update")]
    update_form_class = UpdateForm
    update_view_class = UpdateView
    update_display_class = UpdateDisplay
    delete_decorators = [manage_permission_required("admin_unit:update")]
    delete_form_class = BaseDeleteForm
    list_display_class = ListDisplay

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(AdminUnitInvitation.created_at.desc())
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
