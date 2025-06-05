from flask import url_for
from flask_babel import gettext, lazy_gettext

from project.models import EventReference
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.incoming_event_reference.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.incoming_event_reference.forms import (
    DeleteEventReferenceForm,
    UpdateEventReferenceForm,
)
from project.views.manage_admin_unit.incoming_event_reference.views import ListView


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = EventReference
    create_view_class = None
    read_display_class = ReadDisplay
    update_form_class = UpdateEventReferenceForm
    delete_form_class = DeleteEventReferenceForm
    list_display_class = ListDisplay
    list_view_class = ListView
    generic_prefix = "incoming_"

    def get_model_display_name(self):
        return lazy_gettext("Incoming reference")

    def get_model_display_name_plural(self):
        return lazy_gettext("Incoming references")

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(EventReference.created_at.desc())
        )

    def get_list_per_page(self):
        return 50

    def get_additional_read_actions(self, object):
        result = super().get_additional_read_actions(object)

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
