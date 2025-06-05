from project.models.admin_unit import AdminUnit
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.admin_unit.views import (
    CancelDeletionView,
    RequestDeletionView,
    UpdateView,
    UpdateWidgetView,
)
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitBaseViewHandler,
)
from project.views.utils import current_admin_unit


class ViewHandler(ManageAdminUnitBaseViewHandler):
    model = AdminUnit
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = None

    def get_object_from_kwargs(self, **kwargs):
        return current_admin_unit

    def _add_views(
        self,
        app,
        single_url_folder,
        plural_url_folder,
        single_endpoint_name,
        plural_endpoint_name,
        id_query_arg_name,
    ):
        result = super()._add_views(
            app,
            single_url_folder,
            plural_url_folder,
            single_endpoint_name,
            plural_endpoint_name,
            id_query_arg_name,
        )

        self._add_view(
            "update",
            "/update",
            UpdateView,
            "update",
            app,
        )

        self._add_view(
            "widgets",
            "/widgets",
            UpdateWidgetView,
            "widgets",
            app,
        )

        self._add_view(
            "request_deletion",
            "/request-deletion",
            RequestDeletionView,
            "request_deletion",
            app,
        )

        self._add_view(
            "cancel_deletion",
            "/cancel-deletion",
            CancelDeletionView,
            "cancel_deletion",
            app,
        )

        return result


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
