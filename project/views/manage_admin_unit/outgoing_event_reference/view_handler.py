from flask import url_for
from flask_babel import gettext, lazy_gettext

from project.models import EventReference
from project.models.event import Event
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.outgoing_event_reference.displays import (
    ListDisplay,
)
from project.views.manage_admin_unit.outgoing_event_reference.views import ListView
from project.views.utils import current_admin_unit


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = EventReference
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    list_view_class = ListView
    generic_prefix = "outgoing_"

    def get_model_display_name_plural(self):
        return lazy_gettext("Outgoing references")

    def get_objects_base_query_from_kwargs(self, **kwargs):
        return super().get_objects_base_query_from_kwargs(**kwargs).join(Event)

    def apply_base_filter(self, query, **kwargs):
        return query.filter(Event.admin_unit_id == current_admin_unit.id)

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(EventReference.created_at.desc())
        )

    def get_list_per_page(self):
        return 50

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        view_event_action = self._create_action(
            url_for(
                "event",
                event_id=object.event.id,
            ),
            gettext("View event"),
        )
        if view_event_action:
            result.append(view_event_action)

        return result


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
