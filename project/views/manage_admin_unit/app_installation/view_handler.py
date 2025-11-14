from typing import Annotated

from dependency_injector.wiring import Provide
from flask_babel import gettext

from project.models import AppInstallation
from project.services.app_installation_service import AppInstallationService
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.app_installation.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.app_installation.views import (
    AcceptPermissionsView,
    InstallView,
)
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)


class AppInstallationViewHandler(ManageAdminUnitChildViewHandler):
    model = AppInstallation
    object_service: Annotated[
        AppInstallationService, Provide["services.app_installation_service"]
    ]
    create_view_class = None
    update_view_class = None
    read_display_class = ReadDisplay
    list_display_class = ListDisplay

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
