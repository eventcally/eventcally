from flask import redirect, url_for
from flask_babel import gettext

from project.models import AdminUnitVerificationRequest
from project.services.search_params import AdminUnitVerificationRequestSearchParams
from project.services.verification import get_verification_requests_outgoing_query
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.outgoing_verification_request.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.outgoing_verification_request.views import ListView
from project.views.utils import current_admin_unit, manage_permission_required


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = AdminUnitVerificationRequest
    admin_unit_id_attribute_name = "source_admin_unit_id"
    create_view_class = None
    create_decorators = [manage_permission_required("verification_request:create")]
    read_display_class = ReadDisplay
    read_decorators = [manage_permission_required("verification_request:read")]
    update_view_class = None
    update_decorators = [manage_permission_required("verification_request:update")]
    delete_decorators = [manage_permission_required("verification_request:delete")]
    list_view_class = ListView
    list_display_class = ListDisplay
    list_decorators = [manage_permission_required("verification_request:read")]
    generic_prefix = "outgoing_"

    def check_access(self, **kwargs):
        result = super().check_access(**kwargs)
        if result:  # pragma: no cover
            return result

        if not current_admin_unit.is_verified:
            params = AdminUnitVerificationRequestSearchParams()
            params.source_admin_unit_id = current_admin_unit.id
            request_count = get_verification_requests_outgoing_query(params).count()

            if request_count == 0:
                return redirect(
                    url_for(
                        "manage_admin_unit_verification_requests_outgoing_create_select",
                        id=current_admin_unit.id,
                    )
                )

        return None

    def get_model_display_name_plural(self):
        return gettext("Outgoing verification requests")

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(AdminUnitVerificationRequest.created_at.desc())
        )

    def get_create_url(self, **kwargs):
        return url_for(
            "manage_admin_unit_verification_requests_outgoing_create_select",
            id=current_admin_unit.id,
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
