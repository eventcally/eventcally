from flask_babel import gettext, lazy_gettext

from project.application.queries import GetIncomingEventReferenceQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.incoming_event_reference.views import (
    ListView,
    ReadView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the list and the read page (rating edit and delete as modals) are Vue
    pages (`/bff/manage`)."""

    model_name = "event_reference"
    model_name_plural = "event_references"
    display_name = "Event reference"
    display_name_plural = "Event references"
    create_view_class = None
    read_view_class = ReadView
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView
    generic_prefix = "incoming_"

    def get_model_display_name_plural(self):
        return lazy_gettext("Incoming references")

    def create_get_query(self, object_id):
        return GetIncomingEventReferenceQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__` (the model's display name).
        return f"{gettext(self.display_name)} {object.id}"


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
