from flask_login import current_user

from project.models.admin_unit import AdminUnit
from project.modular.base_view_handler import BaseViewHandler
from project.views.user_blueprint import user_bp
from project.views.user_blueprint.user.views import (
    CancelDeletionView,
    GeneralView,
    NotificationView,
    RequestDeletionView,
)


class ViewHandler(BaseViewHandler):
    model = AdminUnit
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = None

    def get_object_from_kwargs(self, **kwargs):
        return current_user

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

        self._add_view(
            "general",
            "/general",
            GeneralView,
            "general",
            app,
        )

        self._add_view(
            "notifications",
            "/notifications",
            NotificationView,
            "notifications",
            app,
        )

        return result


handler = ViewHandler()
handler.init_app(user_bp)
