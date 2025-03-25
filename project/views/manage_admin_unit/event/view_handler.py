from flask import url_for
from flask_babel import gettext, lazy_gettext

from project.models import Event
from project.modular.ajax import EventCategoryAjaxModelLoader
from project.modular.filters import (
    BooleanFilter,
    DateRangeFilter,
    EnumFilter,
    EventCategoryFilter,
    SelectModelFilter,
    TagFilter,
)
from project.modular.search_definition import SearchDefinition
from project.modular.sort_definition import SortDefinition
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
    UpdateView,
)
from project.views.utils import current_admin_unit, manage_permission_required


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = Event
    create_decorators = [manage_permission_required("event:create")]
    create_view_class = CreateView
    read_view_class = None
    update_decorators = [manage_permission_required("event:update")]
    update_view_class = UpdateView
    delete_decorators = [manage_permission_required("event:delete")]
    delete_view_class = DeleteView
    list_display_class = ListDisplay
    list_filters = [
        EventCategoryFilter(
            Event.categories,
            EventCategoryAjaxModelLoader(),
            key="category_id",
            label=lazy_gettext("Categories"),
        ),
        TagFilter(Event.tags, key="tag", label=lazy_gettext("Tags")),
        SelectModelFilter(
            Event.organizer,
            EventOrganizerAjaxModelLoader(),
            label=lazy_gettext("Organizer"),
        ),
        SelectModelFilter(
            Event.event_place, EventPlaceAjaxModelLoader(), label=lazy_gettext("Place")
        ),
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

    def get_plural_url_folder(self):
        return f"new_{super().get_plural_url_folder()}"

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
                    "event_reference_request_create",
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
