from project.application.queries import GetEventOrganizerForEditQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.event_organizer.views import (
    CreateView,
    UpdateView,
)
from project.presentation.web.views.manage_admin_unit.shell_views import ListShellView


class ViewHandler(ManageAdminUnitChildViewHandler):
    """Shells: the lists, forms and deletes are Vue pages (`/bff/manage`)."""

    model_name = "event_organizer"
    model_name_plural = "event_organizers"
    display_name = "Event organizer"
    display_name_plural = "Event organizers"
    create_view_class = CreateView
    update_view_class = UpdateView
    delete_view_class = None
    read_view_class = None
    list_view_class = ListShellView

    def create_get_query(self, object_id):
        return GetEventOrganizerForEditQuery(id=object_id)


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
