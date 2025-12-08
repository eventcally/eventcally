from typing import Annotated

from dependency_injector.wiring import Provide
from flask import url_for
from flask_babel import gettext, lazy_gettext

from project.models import Event
from project.models.event_place import EventPlace
from project.models.location import Location
from project.modular.ajax import EventCategoryAjaxModelLoader
from project.modular.filters import (
    BooleanFilter,
    DateRangeFilter,
    EnumFilter,
    EventCategoryFilter,
    EventDateRangeFilter,
    PostalCodeFilter,
    RadiusFilter,
    SelectModelFilter,
    TagFilter,
)
from project.modular.search_definition import SearchDefinition
from project.modular.sort_definition import SortDefinition
from project.services.event_service import EventService
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.ajax import (
    EventOrganizerAjaxModelLoader,
    EventPlaceAjaxModelLoader,
)
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.event.displays import ListDisplay
from project.views.manage_admin_unit.event.views import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)
from project.views.utils import current_admin_unit


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = Event
    object_service: Annotated[EventService, Provide["services.event_service"]]
    create_view_class = CreateView
    read_view_class = None
    update_view_class = UpdateView
    delete_view_class = DeleteView
    list_view_class = ListView
    list_display_class = ListDisplay
    list_filters = [
        EventDateRangeFilter(Event.dates, label=lazy_gettext("Date"), key="date"),
        EventCategoryFilter(
            Event.categories,
            EventCategoryAjaxModelLoader(),
            key="category_id",
            label=lazy_gettext("Categories"),
        ),
        TagFilter(Event.tags, key="tag", label=lazy_gettext("Tags")),
        TagFilter(
            Event.internal_tags, key="internal_tag", label=lazy_gettext("Internal tags")
        ),
        SelectModelFilter(
            Event.organizer,
            EventOrganizerAjaxModelLoader(),
            label=lazy_gettext("Organizer"),
        ),
        SelectModelFilter(
            Event.event_place, EventPlaceAjaxModelLoader(), label=lazy_gettext("Place")
        ),
        PostalCodeFilter(
            Location.postalCode, key="postal_code", label=lazy_gettext("Postal code")
        ),
        RadiusFilter(Location.coordinate, key="radius", label=lazy_gettext("Radius")),
        EnumFilter(Event.status, label=lazy_gettext("Status")),
        EnumFilter(Event.public_status, label=lazy_gettext("Public status")),
        DateRangeFilter(Event.created_at, label=lazy_gettext("Created at")),
        BooleanFilter(Event.is_recurring, label=lazy_gettext("Recurring event")),
    ]
    list_sort_definitions = [
        SortDefinition(Event.min_start, label=lazy_gettext("Earliest start first")),
        SortDefinition(
            Event.last_modified_at,
            desc=True,
            label=lazy_gettext("Last modified first"),
        ),
        SortDefinition(
            Event.created_at,
            desc=True,
            label=lazy_gettext("Newest first"),
        ),
    ]
    list_search_definitions = [SearchDefinition(Event.name)]

    def get_objects_base_query_from_kwargs(self, **kwargs):
        query = super().get_objects_base_query_from_kwargs(**kwargs)
        return (
            query.join(Event.event_place, isouter=True)
            .join(EventPlace.location, isouter=True)
            .join(Event.organizer, isouter=True)
        )

    def get_list_per_page(self):
        return 50

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        view_action = self._create_action(
            url_for(
                "event",
                event_id=object.id,
            ),
            gettext("View"),
        )
        if view_action:
            result.append(view_action)

        if object.admin_unit_id == current_admin_unit.id:
            reference_request_create_action = self._create_action(
                url_for(
                    "manage_admin_unit.outgoing_event_reference_request_create_for_event",
                    id=object.admin_unit_id,
                    event_id=object.id,
                ),
                gettext("Request reference"),
            )
            if reference_request_create_action:
                result.append(reference_request_create_action)
        else:  # pragma: no cover
            reference_create_action = self._create_action(
                url_for(
                    "event_reference_create",
                    event_id=object.id,
                ),
                gettext("Reference event"),
            )
            if reference_create_action:
                result.append(reference_create_action)

        actions_action = self._create_action(
            url_for(
                "event_actions",
                event_id=object.id,
            ),
            gettext("More"),
        )
        if actions_action:
            result.append(actions_action)

        return result


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
