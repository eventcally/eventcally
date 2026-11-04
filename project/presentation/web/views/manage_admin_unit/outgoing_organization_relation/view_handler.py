from flask_babel import lazy_gettext

from project.application.queries import GetOutgoingOrganizationRelationQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.outgoing_organization_relation.views import (
    CreateView,
    ListView,
    UpdateView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list and the forms are Vue pages (`/bff/manage`); deleting is a
    modal of the list."""

    model_name = "organization_relation"
    model_name_plural = "organization_relations"
    display_name = "Organization relation"
    display_name_plural = "Organization relations"
    admin_unit_id_attribute_name = "source_admin_unit_id"
    create_view_class = CreateView
    read_view_class = None
    update_view_class = UpdateView
    delete_view_class = None
    list_view_class = ListView
    generic_prefix = "outgoing_"

    def get_model_display_name(self):
        return lazy_gettext("Outgoing organization relation")

    def get_model_display_name_plural(self):
        return lazy_gettext("Outgoing organization relations")

    def create_get_query(self, object_id):
        return GetOutgoingOrganizationRelationQuery(id=object_id)


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
