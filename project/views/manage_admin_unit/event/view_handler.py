from flask import url_for
from flask_babel import gettext, lazy_gettext

from project.application.queries import (
    EventSearchCriteria,
    EventSearchSort,
    GetEventForEditQuery,
    SearchEventsQuery,
    TrackableCriteria,
)
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.modular.ajax import EventCategoryAjaxModelLoader
from project.modular.filters import (
    KeyBooleanFilter,
    KeyDateRangeFilter,
    KeyEnumFilter,
    KeyRadiusFilter,
    KeySelectModelFilter,
    KeyTagFilter,
    enum_filter_value_or_none,
)
from project.modular.search_definition import KeySearchDefinition
from project.modular.sort_definition import KeySortDefinition
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
    model_name = "event"
    model_name_plural = "events"
    display_name = "Event"
    display_name_plural = "Events"
    create_view_class = CreateView
    read_view_class = None
    update_view_class = UpdateView
    delete_view_class = DeleteView
    list_view_class = ListView
    list_display_class = ListDisplay
    list_filters = [
        KeyDateRangeFilter("date", label=lazy_gettext("Date")),
        KeySelectModelFilter(
            "category_id",
            EventCategoryAjaxModelLoader(),
            label=lazy_gettext("Categories"),
        ),
        KeyTagFilter("tag", label=lazy_gettext("Tags")),
        KeyTagFilter("internal_tag", label=lazy_gettext("Internal tags")),
        KeySelectModelFilter(
            "organizer_id",
            EventOrganizerAjaxModelLoader(),
            label=lazy_gettext("Organizer"),
        ),
        KeySelectModelFilter(
            "event_place_id",
            EventPlaceAjaxModelLoader(),
            label=lazy_gettext("Place"),
        ),
        KeyTagFilter("postal_code", label=lazy_gettext("Postal code")),
        KeyRadiusFilter("radius", label=lazy_gettext("Radius")),
        KeyEnumFilter("status", EventStatus, label=lazy_gettext("Status")),
        KeyEnumFilter(
            "public_status", EventPublicStatus, label=lazy_gettext("Public status")
        ),
        KeyDateRangeFilter("created_at", label=lazy_gettext("Created at")),
        KeyBooleanFilter("is_recurring", label=lazy_gettext("Recurring event")),
    ]
    list_sort_definitions = [
        KeySortDefinition("min_start", label=lazy_gettext("Earliest start first")),
        KeySortDefinition(
            "-last_modified_at", label=lazy_gettext("Last modified first")
        ),
        KeySortDefinition("-created_at", label=lazy_gettext("Newest first")),
    ]
    list_search_definitions = [KeySearchDefinition("name")]

    def create_list_query(self, form, page_request, **kwargs):
        postal_codes = _split(form.postal_code.data)
        radius = form.radius.form
        coordinate = radius.coordinate.data
        latitude = longitude = distance = None

        if coordinate and len(coordinate) > 1 and radius.distance.data:
            latitude, longitude = coordinate.split(",")
            distance = radius.distance.data

        status = enum_filter_value_or_none(EventStatus, form.status.data)
        public_status = enum_filter_value_or_none(
            EventPublicStatus, form.public_status.data
        )
        is_recurring = {"1": True, "0": False}.get(form.is_recurring.data)

        criteria = EventSearchCriteria(
            admin_unit_id=current_admin_unit.id,
            include_private=True,
            name=form.keyword.data or None,
            date_from=form.date.form.from_field.data or None,
            date_to=form.date.form.to_field.data or None,
            category_ids=[form.category_id.data.id] if form.category_id.data else [],
            tags=_split(form.tag.data),
            internal_tags=_split(form.internal_tag.data),
            organizer_id=form.organizer_id.data.id if form.organizer_id.data else None,
            event_place_id=(
                form.event_place_id.data.id if form.event_place_id.data else None
            ),
            postal_codes=postal_codes,
            latitude=latitude,
            longitude=longitude,
            distance=distance,
            status=[status] if status else [],
            public_status=[public_status] if public_status else [],
            is_recurring=is_recurring,
            trackable=TrackableCriteria(
                created_at_from=form.created_at.form.from_field.data or None,
                created_at_to=form.created_at.form.to_field.data or None,
            ),
            sort=_SORTS.get(form.sort.data),
        )
        return SearchEventsQuery(
            criteria=criteria,
            reference_admin_unit_id=current_admin_unit.id,
            include_counts=True,
            page=page_request,
        )

    def create_get_query(self, object_id):
        return GetEventForEditQuery(id=object_id)

    def get_object_title(self, object):
        return object.name

    def get_list_per_page(self):
        return 50

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        view_action = self._create_action(
            url_for(
                "main.event",
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
                "main.event_actions",
                event_id=object.id,
            ),
            gettext("More"),
        )
        if actions_action:
            result.append(actions_action)

        return result


_SORTS = {
    "-last_modified_at": EventSearchSort.last_modified_at_desc,
    "-created_at": EventSearchSort.created_at_desc,
}


def _split(value) -> list:
    """Comma separated form input; unknown sort keys fall back to the default order
    through `_SORTS`, as the ORM path did."""
    return [item for item in value.split(",") if item] if value else []


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
