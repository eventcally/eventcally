from typing import Annotated

from dependency_injector.wiring import Provide
from flask_babel import lazy_gettext

from project.access import admin_unit_owner_access_or_401
from project.models import EventReferenceRequest
from project.models.event import Event
from project.modular.filters import EnumFilter
from project.modular.sort_definition import SortDefinition
from project.services.event_reference_request_service import (
    EventReferenceRequestService,
)
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.outgoing_event_reference_request.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.outgoing_event_reference_request.views import (
    CreateView,
    ListView,
)
from project.views.utils import current_admin_unit


class ViewHandler(ManageAdminUnitChildViewHandler):
    admin_unit_id_attribute_name = None
    model = EventReferenceRequest
    object_service: Annotated[
        EventReferenceRequestService,
        Provide["services.event_reference_request_service"],
    ]
    create_view_class = None
    read_display_class = ReadDisplay
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    list_view_class = ListView
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
        return lazy_gettext("Outgoing reference requests")

    def get_objects_base_query_from_kwargs(self, **kwargs):
        return super().get_objects_base_query_from_kwargs(**kwargs).join(Event)

    def apply_base_filter(self, query, **kwargs):
        return query.filter(Event.admin_unit_id == current_admin_unit.id)

    def get_list_per_page(self):
        return 50

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
