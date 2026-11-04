from project.application.queries import GetApiKeyQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.api_key.views import (
    CreateView,
    ListView,
    ReadView,
)
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)


class ApiKeyViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list, the create form and the read page are Vue pages
    (`/bff/manage`); renaming and deleting are modals of the read page / list."""

    model_name = "api_key"
    model_name_plural = "api_keys"
    display_name = "API key"
    display_name_plural = "API keys"
    create_view_class = CreateView
    read_view_class = ReadView
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView

    def create_get_query(self, object_id):
        return GetApiKeyQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"


handler = ApiKeyViewHandler()
handler.init_app(manage_admin_unit_bp)
