from flask_babel import gettext
from sqlalchemy import func

from project.models import AdminUnitRelation
from project.models.admin_unit import AdminUnit
from project.modular.base_form import BaseDeleteForm
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.outgoing_organization_relation.displays import (
    ListDisplay,
    UpdateDisplay,
)
from project.views.manage_admin_unit.outgoing_organization_relation.forms import (
    CreateForm,
    UpdateForm,
)
from project.views.manage_admin_unit.outgoing_organization_relation.views import (
    CreateView,
    UpdateView,
)
from project.views.utils import manage_permission_required


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = AdminUnitRelation
    admin_unit_id_attribute_name = "source_admin_unit_id"
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
    generic_prefix = "outgoing_"

    def get_model_display_name(self):
        return gettext("Outgoing organization relation")

    def get_model_display_name_plural(self):
        return gettext("Outgoing organization relations")

    def get_objects_base_query_from_kwargs(self, **kwargs):
        return (
            super()
            .get_objects_base_query_from_kwargs(**kwargs)
            .join(AdminUnit, AdminUnitRelation.target_admin_unit_id == AdminUnit.id)
        )

    def apply_objects_query_order(self, query, **kwargs):
        return query.order_by(func.lower(AdminUnit.name))


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
