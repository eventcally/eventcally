from project.models.admin_unit import AdminUnit
from project.modular.base_view_handler import BaseViewHandler
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.admin_unit.forms import (
    CancelDeletionForm,
    RequestDeletionForm,
    UpdateForm,
    UpdateWidgetForm,
)
from project.views.manage_admin_unit.admin_unit.views import (
    CancelDeletionView as _CancelDeletionView,
)
from project.views.manage_admin_unit.admin_unit.views import (
    RequestDeletionView as _RequestDeletionView,
)
from project.views.manage_admin_unit.admin_unit.views import UpdateView as _UpdateView
from project.views.manage_admin_unit.admin_unit.views import (
    UpdateWidgetView as _UpdateWidgetView,
)
from project.views.utils import current_admin_unit, manage_permission_required


class ViewHandler(BaseViewHandler):
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

        class UpdateView(_UpdateView):
            decorators = [manage_permission_required("admin_unit:update")]
            form_class = UpdateForm

        self._add_view(
            "update",
            "/update",
            UpdateView,
            "update",
            app,
        )

        class UpdateWidgetView(_UpdateWidgetView):
            decorators = [manage_permission_required("admin_unit:update")]
            form_class = UpdateWidgetForm

        self._add_view(
            "widgets",
            "/widgets",
            UpdateWidgetView,
            "widgets",
            app,
        )

        class RequestDeletionView(_RequestDeletionView):
            decorators = [manage_permission_required("admin_unit:update")]
            form_class = RequestDeletionForm

        self._add_view(
            "request_deletion",
            "/request-deletion",
            RequestDeletionView,
            "request_deletion",
            app,
        )

        class CancelDeletionView(_CancelDeletionView):
            decorators = [manage_permission_required("admin_unit:update")]
            form_class = CancelDeletionForm

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
