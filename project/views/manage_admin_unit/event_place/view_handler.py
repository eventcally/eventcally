from typing import Annotated

from dependency_injector.wiring import Provide
from flask import flash, url_for
from flask_babel import gettext, lazy_gettext
from sqlalchemy import func

from project.models import EventPlace
from project.modular.search_definition import SearchDefinition
from project.modular.sort_definition import SortDefinition
from project.services.event_place_service import EventPlaceService
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.event_place.displays import ListDisplay
from project.views.manage_admin_unit.event_place.forms import (
    CreateEventPlaceForm,
    DeleteEventPlaceForm,
    UpdateEventPlaceForm,
)
from project.views.utils import current_admin_unit, non_match_for_deletion


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = EventPlace
    object_service: Annotated[
        EventPlaceService, Provide["services.event_place_service"]
    ]
    create_form_class = CreateEventPlaceForm
    read_view_class = None
    update_form_class = UpdateEventPlaceForm
    delete_form_class = DeleteEventPlaceForm
    list_display_class = ListDisplay
    list_sort_definitions = [
        SortDefinition(EventPlace.name, func=func.lower, label=lazy_gettext("Name")),
        SortDefinition(
            EventPlace.last_modified_at,
            desc=True,
            label=lazy_gettext("Last modified first"),
        ),
        SortDefinition(
            EventPlace.number_of_events,
            desc=True,
            label=lazy_gettext("Number of events"),
        ),
    ]
    list_search_definitions = [SearchDefinition(EventPlace.name)]

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


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
