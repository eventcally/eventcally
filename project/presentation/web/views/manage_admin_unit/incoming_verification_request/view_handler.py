from flask_babel import lazy_gettext

from project.application.queries import (
    GetIncomingOrganizationVerificationRequestReviewQuery,
)
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.incoming_verification_request.views import (
    ListView,
    ReviewView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list and the review page are Vue pages (`/bff/manage`)."""

    model_name = "organization_verification_request"
    model_name_plural = "organization_verification_requests"
    display_name = "Organization verification request"
    display_name_plural = "Organization verification requests"
    admin_unit_id_attribute_name = "target_admin_unit_id"
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView
    generic_prefix = "incoming_"

    def create_get_query(self, object_id):
        return GetIncomingOrganizationVerificationRequestReviewQuery(id=object_id)

    def get_model_display_name_plural(self):
        return lazy_gettext("Incoming verification requests")

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
            "review",
            f"/{single_url_folder}/<int:{id_query_arg_name}>/review",
            ReviewView,
            f"{single_endpoint_name}_review",
            app,
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
