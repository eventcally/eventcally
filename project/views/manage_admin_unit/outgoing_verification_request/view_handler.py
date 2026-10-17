from flask import redirect, url_for
from flask_babel import lazy_gettext

from project.application.queries import (
    GetOutgoingOrganizationVerificationRequestQuery,
    ListOutgoingOrganizationVerificationRequestsQuery,
    PageRequest,
)
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.outgoing_verification_request.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.outgoing_verification_request.views import (
    DeleteView,
    ListView,
)
from project.views.utils import current_admin_unit


class ViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "organization_verification_request"
    model_name_plural = "organization_verification_requests"
    display_name = "Organization verification request"
    display_name_plural = "Organization verification requests"
    admin_unit_id_attribute_name = "source_admin_unit_id"
    create_view_class = None
    read_display_class = ReadDisplay
    update_view_class = None
    delete_view_class = DeleteView
    list_view_class = ListView
    list_display_class = ListDisplay
    generic_prefix = "outgoing_"

    def check_access(self, **kwargs):
        result = super().check_access(**kwargs)
        if result:  # pragma: no cover
            return result

        if not current_admin_unit.is_verified:
            requests = self.query_bus.handle(
                ListOutgoingOrganizationVerificationRequestsQuery(
                    admin_unit_id=current_admin_unit.id,
                    page=PageRequest(page=1, per_page=1),
                )
            )

            if requests.total == 0:
                return redirect(
                    url_for(
                        "main.manage_organization_verification_requests_outgoing_create_select",
                        id=current_admin_unit.id,
                    )
                )

        return None

    def get_model_display_name_plural(self):
        return lazy_gettext("Outgoing verification requests")

    def create_list_query(self, form, page_request, **kwargs):
        return ListOutgoingOrganizationVerificationRequestsQuery(
            admin_unit_id=current_admin_unit.id, page=page_request
        )

    def create_get_query(self, object_id):
        return GetOutgoingOrganizationVerificationRequestQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"

    def get_create_url(self, **kwargs):
        return url_for(
            "main.manage_organization_verification_requests_outgoing_create_select",
            id=current_admin_unit.id,
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
