from flask_babel import gettext, lazy_gettext

from project.access import admin_unit_owner_access_or_401
from project.models import EventReferenceRequest
from project.models.event import Event
from project.modular.filters import EnumFilter
from project.modular.sort_definition import SortDefinition
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.outgoing_event_reference_request.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.outgoing_event_reference_request.views import (
    ListView,
)
from project.views.utils import current_admin_unit, manage_permission_required


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = EventReferenceRequest
    create_view_class = None
    read_display_class = ReadDisplay
    read_decorators = [manage_permission_required("reference_request:read")]
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    list_view_class = ListView
    list_decorators = [manage_permission_required("reference_request:read")]
    list_filters = [
        EnumFilter(
            EventReferenceRequest.review_status, label=lazy_gettext("Review status")
        ),
    ]
    list_sort_definitions = [
        SortDefinition(
            EventReferenceRequest.created_at,
            desc=True,
            label=lazy_gettext("Last created first"),
        ),
    ]
    generic_prefix = "outgoing_"

    def check_object_access(self, object):
        return admin_unit_owner_access_or_401(object.event.admin_unit_id)

    def get_model_display_name_plural(self):
        return gettext("Outgoing reference requests")

    def get_objects_base_query_from_kwargs(self, **kwargs):
        return super().get_objects_base_query_from_kwargs(**kwargs).join(Event)

    def apply_base_filter(self, query, **kwargs):
        return query.filter(Event.admin_unit_id == current_admin_unit.id)

    def get_list_per_page(self):
        return 50


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
