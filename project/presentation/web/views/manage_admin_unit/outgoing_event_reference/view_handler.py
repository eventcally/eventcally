from flask_babel import lazy_gettext

from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.outgoing_event_reference.views import (
    ListView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    """A shell: the list is a Vue page (`/bff/manage`)."""

    model_name = "event_reference"
    model_name_plural = "event_references"
    display_name = "Event reference"
    display_name_plural = "Event references"
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView
    generic_prefix = "outgoing_"

    def get_model_display_name_plural(self):
        return lazy_gettext("Outgoing references")


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
