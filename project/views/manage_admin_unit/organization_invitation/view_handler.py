from typing import Annotated

from dependency_injector.wiring import Provide

from project.models import AdminUnitInvitation
from project.modular.base_form import BaseDeleteForm
from project.services.organization_invitation_service import (
    OrganizationInvitationService,
)
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


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = AdminUnitInvitation
    object_service: Annotated[
        OrganizationInvitationService,
        Provide["services.organization_invitation_service"],
    ]
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
            .order_by(AdminUnitInvitation.created_at.desc())
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
