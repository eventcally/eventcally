from project.application.queries import GetEventForEditQuery
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.event.views import (
    CreateView,
    DeleteView,
    UpdateView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "event"
    model_name_plural = "events"
    display_name = "Event"
    display_name_plural = "Events"
    create_view_class = CreateView
    read_view_class = None
    update_view_class = UpdateView
    delete_view_class = DeleteView
    list_view_class = None

    def create_get_query(self, object_id):
        return GetEventForEditQuery(id=object_id)


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
