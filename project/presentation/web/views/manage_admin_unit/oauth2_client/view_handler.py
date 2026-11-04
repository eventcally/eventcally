from project.application.queries import GetOAuth2ClientQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.oauth2_client.views import (
    CreateView,
    ListView,
    ReadView,
    UpdateView,
)


class OAuth2ClientViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list, the read page and the form are Vue pages (`/bff/manage`);
    deleting is a modal."""

    model_name = "oauth2_client"
    model_name_plural = "oauth2_clients"
    display_name = "OAuth2 client"
    display_name_plural = "OAuth2 clients"
    create_view_class = CreateView
    read_view_class = ReadView
    update_view_class = UpdateView
    delete_view_class = None
    list_view_class = ListView

    def create_get_query(self, object_id):
        return GetOAuth2ClientQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `OAuth2Client.__str__`.
        return object.client_name or f"{self.get_model_display_name()} {object.id}"


handler = OAuth2ClientViewHandler()
handler.init_app(manage_admin_unit_bp)
