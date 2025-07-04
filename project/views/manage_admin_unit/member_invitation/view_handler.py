from sqlalchemy.sql import func

from project.models import AdminUnitMemberInvitation
from project.modular.base_form import BaseDeleteForm
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.member_invitation.displays import (
    ListDisplay,
    UpdateDisplay,
)
from project.views.manage_admin_unit.member_invitation.forms import (
    CreateForm,
    UpdateForm,
)
from project.views.manage_admin_unit.member_invitation.views import (
    CreateView,
    UpdateView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = AdminUnitMemberInvitation
    create_form_class = CreateForm
    create_view_class = CreateView
    read_view_class = None
    update_form_class = UpdateForm
    update_view_class = UpdateView
    update_display_class = UpdateDisplay
    delete_form_class = BaseDeleteForm
    list_display_class = ListDisplay

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(func.lower(AdminUnitMemberInvitation.email))
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
