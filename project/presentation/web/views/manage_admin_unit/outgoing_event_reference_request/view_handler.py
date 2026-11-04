from flask_babel import lazy_gettext

from project.application.queries import GetOutgoingEventReferenceRequestQuery
from project.presentation.shared.access import admin_unit_owner_access_or_401
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.outgoing_event_reference_request.views import (
    CreateView,
    ListView,
    ReadView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    admin_unit_id_attribute_name = None
    model_name = "event_reference_request"
    model_name_plural = "event_reference_requests"
    display_name = "Event reference request"
    display_name_plural = "Event reference requests"
    create_view_class = None
    read_view_class = ReadView
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView
    generic_prefix = "outgoing_"

    def check_object_access(self, object):
        return admin_unit_owner_access_or_401(object.event.admin_unit.id)

    def get_model_display_name_plural(self):
        return lazy_gettext("Outgoing reference requests")

    def create_get_query(self, object_id):
        return GetOutgoingEventReferenceRequestQuery(id=object_id)

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
            "create_for_event",
            f"/{single_url_folder}/create_for_event/<int:event_id>",
            CreateView,
            f"{single_endpoint_name}_create_for_event",
            app,
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
