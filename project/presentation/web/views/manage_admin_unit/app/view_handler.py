from flask_babel import gettext

from project.application.queries import GetAppQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.app.views import (
    CreateView,
    ListView,
    ReadView,
    UpdateView,
)
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)


class AppViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list, the read page (with the keys) and the form are Vue pages
    (`/bff/manage`); deleting is a modal."""

    model_name = "app"
    model_name_plural = "apps"
    display_name = "App"
    display_name_plural = "Apps"
    create_view_class = CreateView
    read_view_class = ReadView
    update_view_class = UpdateView
    delete_view_class = None
    list_view_class = ListView

    def create_get_query(self, object_id):
        return GetAppQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `OAuth2Client.__str__`.
        return object.client_name or f"{gettext('OAuth2 client')} {object.id}"


handler = AppViewHandler()
handler.init_app(manage_admin_unit_bp)
