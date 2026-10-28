from flask import url_for

from project.application.queries import GetEventForEditQuery
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.event_legacy.views import (
    CreateView,
    UpdateView,
)


class LegacyViewHandler(ManageAdminUnitChildViewHandler):
    """The previous WTForms event form under `/legacy/event/...`, reachable from the Vue
    form. `model_name` stays `event`, so the permission (`events:write`) and the URL
    argument (`event_id`) are the same; only the URL folder, endpoints and templates
    differ (not `generic_prefix`, which would change the permission entity too)."""

    model_name = "event"
    model_name_plural = "events"
    display_name = "Event"
    display_name_plural = "Events"
    create_view_class = CreateView
    read_view_class = None
    update_view_class = UpdateView
    delete_view_class = None
    list_view_class = None

    def create_get_query(self, object_id):
        return GetEventForEditQuery(id=object_id)

    def get_list_url(self, **kwargs):
        return url_for("manage_admin_unit.events", id=current_admin_unit.id)

    def get_single_url_folder(self):
        return "legacy/event"

    def get_single_endpoint_name(self):
        return "event_legacy"

    def get_template_folder(self):
        return "event_legacy"


handler = LegacyViewHandler()
handler.init_app(manage_admin_unit_bp)
