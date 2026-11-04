from flask_babel import lazy_gettext

from project.application.queries import GetOutgoingOrganizationVerificationRequestQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.outgoing_verification_request.views import (
    ListView,
    ReadView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list and the read page are Vue pages (`/bff/manage`); requesting
    and withdrawing are modals of the list / read page."""

    model_name = "organization_verification_request"
    model_name_plural = "organization_verification_requests"
    display_name = "Organization verification request"
    display_name_plural = "Organization verification requests"
    admin_unit_id_attribute_name = "source_admin_unit_id"
    create_view_class = None
    read_view_class = ReadView
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView
    generic_prefix = "outgoing_"

    def get_model_display_name_plural(self):
        return lazy_gettext("Outgoing verification requests")

    def create_get_query(self, object_id):
        return GetOutgoingOrganizationVerificationRequestQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
