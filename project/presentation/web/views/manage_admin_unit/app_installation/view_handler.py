from project.application.queries import GetAppInstallationQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.app_installation.views import (
    InstallView,
    ListView,
    ReadView,
)
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)


class AppInstallationViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list, the read page (with accepting new permissions) and the install
    page are Vue pages (`/bff/manage`); uninstalling is a modal."""

    model_name = "app_installation"
    model_name_plural = "app_installations"
    display_name = "App installation"
    display_name_plural = "App installations"
    create_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView
    read_view_class = ReadView

    def create_get_query(self, object_id):
        return GetAppInstallationQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"

    def _add_views(
        self,
        app,
        single_url_folder,
        plural_url_folder,
        single_endpoint_name,
        plural_endpoint_name,
        id_query_arg_name,
    ):
        super()._add_views(
            app,
            single_url_folder,
            plural_url_folder,
            single_endpoint_name,
            plural_endpoint_name,
            id_query_arg_name,
        )

        self._add_view(
            "install",
            f"/{plural_url_folder}/install/<int:app_id>",
            InstallView,
            f"{plural_endpoint_name}_install",
            app,
        )


handler = AppInstallationViewHandler()
handler.init_app(manage_admin_unit_bp)
