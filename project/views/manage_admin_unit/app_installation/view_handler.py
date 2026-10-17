from flask_babel import gettext

from project.application.queries import (
    GetAppInstallationQuery,
    ListAppInstallationsQuery,
)
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.app_installation.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.app_installation.views import (
    AcceptPermissionsView,
    DeleteView,
    InstallView,
)
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.utils import current_admin_unit


class AppInstallationViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "app_installation"
    model_name_plural = "app_installations"
    display_name = "App installation"
    display_name_plural = "App installations"
    create_view_class = None
    update_view_class = None
    delete_view_class = DeleteView
    read_display_class = ReadDisplay
    list_display_class = ListDisplay

    def create_list_query(self, form, page_request, **kwargs):
        return ListAppInstallationsQuery(
            admin_unit_id=current_admin_unit.id, page=page_request
        )

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
        self._add_view(
            "accept_permissions",
            f"/{single_url_folder}/<int:{id_query_arg_name}>/accept_permissions",
            AcceptPermissionsView,
            f"{single_endpoint_name}_accept_permissions",
            app,
        )

    def get_additional_read_actions(self, object):
        result = super().get_additional_read_actions(object)
        result.append(
            self._create_action(
                self._get_object_url("accept_permissions", object),
                gettext("Accept permissions"),
            )
        )
        return result


handler = AppInstallationViewHandler()
handler.init_app(manage_admin_unit_bp)
