from flask import flash, url_for
from flask_babel import gettext, lazy_gettext

from project.application.queries import (
    EventPlaceSort,
    GetEventPlaceForEditQuery,
    ListEventPlacesQuery,
)
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.modular.search_definition import KeySearchDefinition
from project.presentation.web.modular.sort_definition import KeySortDefinition
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.event_place.displays import (
    ListDisplay,
)
from project.presentation.web.views.manage_admin_unit.event_place.views import (
    CreateView,
    DeleteView,
    UpdateView,
)
from project.presentation.web.views.utils import non_match_for_deletion


class ViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "event_place"
    model_name_plural = "event_places"
    display_name = "Place"
    display_name_plural = "Places"
    create_view_class = CreateView
    update_view_class = UpdateView
    delete_view_class = DeleteView
    read_view_class = None
    list_display_class = ListDisplay
    list_sort_definitions = [
        KeySortDefinition(EventPlaceSort.name.value, label=lazy_gettext("Name")),
        KeySortDefinition(
            EventPlaceSort.last_modified_at_desc.value,
            label=lazy_gettext("Last modified first"),
        ),
        KeySortDefinition(
            EventPlaceSort.number_of_events_desc.value,
            label=lazy_gettext("Number of events"),
        ),
    ]
    list_search_definitions = [KeySearchDefinition("name")]

    def create_list_query(self, form, page_request, **kwargs):
        return ListEventPlacesQuery(
            admin_unit_id=current_admin_unit.id,
            keyword=form.keyword.data or None,
            sort=_sort_or_none(form.sort.data),
            page=page_request,
        )

    def create_get_query(self, object_id):
        return GetEventPlaceForEditQuery(id=object_id)

    def get_object_title(self, object):
        return object.name

    def get_list_per_page(self):
        return 50

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        view_events_action = self._create_action(
            url_for(
                "manage_admin_unit.events",
                id=current_admin_unit.id,
                event_place_id=object.id,
            ),
            gettext("View events"),
        )
        if view_events_action:
            result.append(view_events_action)

        return result

    def can_object_be_deleted(self, form, object):
        if non_match_for_deletion(form.name.data, object.name):
            flash(gettext("Entered name does not match place name"), "danger")
            return False
        return True


def _sort_or_none(value):
    """Unknown sort keys fall back to the default order, as the ORM path did."""
    try:
        return EventPlaceSort(value)
    except ValueError:
        return None


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
