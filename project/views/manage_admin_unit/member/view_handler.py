from flask import url_for
from sqlalchemy.sql import func

from project.models import AdminUnitMember
from project.models.user import User
from project.modular.base_form import BaseDeleteForm
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.member.displays import ListDisplay, UpdateDisplay
from project.views.manage_admin_unit.member.forms import UpdateForm
from project.views.manage_admin_unit.member.views import DeleteView, UpdateView


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = AdminUnitMember
    create_view_class = None
    read_view_class = None
    update_form_class = UpdateForm
    update_view_class = UpdateView
    update_display_class = UpdateDisplay
    delete_form_class = BaseDeleteForm
    delete_view_class = DeleteView
    list_display_class = ListDisplay

    def get_objects_base_query_from_kwargs(self, **kwargs):
        return super().get_objects_base_query_from_kwargs(**kwargs).join(User)

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(func.lower(User.email))
        )

    def get_create_url(self, **kwargs):
        return url_for(
            "manage_admin_unit.organization_member_invitation_create",
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
